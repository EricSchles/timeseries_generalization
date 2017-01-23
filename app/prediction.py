import pandas as pd
import math
import datetime
import statsmodels.api as sm
import statistics
from functools import partial
import code
from scipy.optimize import brute
import matplotlib.pyplot as plt
import numpy as np
import asyncio
from app.models import Prediction, EventInformation, Trend
from app import db

# this comes from here:
# http://stackoverflow.com/questions/22770352/auto-arima-equivalent-for-python
def objective_function(data, order):
    return sm.tsa.ARIMA(data, order).fit(disp=0).aic


def brute_search(data):
    print("got here with no errors")
    obj_func = partial(objective_function, data)
    # Back in graduate school professor Lecun said in class that ARIMA models
    # typically only need a max parameter of 5, so I doubled it just in case.
    upper_bound_AR = 10
    upper_bound_I = 10
    upper_bound_MA = 10
    grid_not_found = True
    while grid_not_found:
        try:
            if upper_bound_AR < 0 or upper_bound_I < 0 or upper_bound_MA < 0:
                grid_not_found = False
            grid = (
                slice(1, upper_bound_AR, 1),
                slice(1, upper_bound_I, 1),
                slice(1, upper_bound_MA, 1)
            )
            order = brute(obj_func, grid, finish=None)
            return order

        except Exception as e:
            error_string = str(e)
            if "MA" in error_string:
                upper_bound_MA -= 1
            elif "AR" in error_string:
                upper_bound_AR -= 1
            else:
                upper_bound_I -= 1

    # assuming we don't ever hit a reasonable set of upper_bounds,
    # it's pretty safe to assume this will work
    try:
        grid = (
            slice(1, 2, 1),
            slice(1, 2, 1),
            slice(1, 2, 1)
        )
        order = brute(obj_func, grid, finish=None)
        return order

    except:  # however we don't always meet invertibility conditions
        # Here we explicitly test for a single MA
        # or AR process being a better fit
        # If either has a lower (better) aic score we return that model order
        try:
            model_ar_one = sm.tsa.ARIMA(data, (1, 0, 0)).fit(disp=0)
            model_ma_one = sm.tsa.ARIMA(data, (0, 0, 1)).fit(disp=0)
        except:
            return None
        if model_ar_one.aic < model_ma_one.aic:
            return (1, 0, 0)
        else:
            return (0, 0, 1)


def date_to_datetime(time_string):
    return datetime.datetime.strptime(time_string, '%m/%d/%Y')

    
# create a monthly continuous time series to pull from
# interpolate values from trend
# set prediction from new values from artificially generated time series.


def check_for_extreme_values(sequence, sequence_to_check=None):
    print("started check")
    data = [sequence.ix[i].Price for i in sequence.index]
    print("moved things to a list")
    final_data = []
    for elem in data:
        try:
            len(elem)
            for i in range(len(elem)):
                final_data.append(float(elem[i]))
        except:
            final_data.append(elem)
    print("finished for loop")
    print("finished post processing")
    sequence = final_data[:]
    mean = statistics.mean(sequence)
    stdev = statistics.stdev(sequence)
    if sequence_to_check is not None:
        for val in sequence_to_check:
            if val >= mean + (stdev*2):
                sequence_to_check.remove(val)
            elif val <= mean - (stdev*2):
                sequence_to_check.remove(val)
        return sequence_to_check
    else:
        for val in sequence:
            if val >= mean + (stdev*2):
                return True
            elif val <= mean - (stdev*2):
                return True
        return False


def remove_extreme_values(sequence, sequence_to_check=None):
    
    data = [float(sequence.ix[i]) for i in sequence.index]
    print("moved things to a list")
    
    mean = statistics.mean(data)
    stdev = statistics.stdev(data)
    print("created mean, std")
    new_sequence = sequence.copy()
    for ind,val in enumerate(data):
        if val >= mean + (stdev*2):
            new_sequence = new_sequence.drop(sequence.index[ind])
        elif val <= mean - (stdev*2):
            new_sequence = new_sequence.drop(sequence.index[ind])
    print("removed bad values")
    return new_sequence

    
def clean_data(data, to_predict):
    if to_predict == "number_attendees":
        new_data = pd.DataFrame()
        for timestamp in set(data.index):
            if len(data.ix[timestamp]) > 1:
                tmp_df = data.ix[timestamp].copy()
                new_price = statistics.median([tmp_df.iloc[index]["number_attendees"] for index in range(len(tmp_df))])
                series = tmp_df.iloc[0]
                series["number_attendees"] = new_price
                new_data = new_data.append(series)
            else:
                new_data = new_data.append(data.ix[timestamp])
        return new_data
    else:
        new_data = pd.DataFrame()
        for timestamp in set(data.index):
            if len(data.ix[timestamp]) > 1:
                tmp_df = data.ix[timestamp].copy()
                new_price = statistics.median([tmp_df.iloc[index]["number_applications"] for index in range(len(tmp_df))])
                series = tmp_df.iloc[0]
                series["number_applications"] = new_price
                new_data = new_data.append(series)
            else:
                new_data = new_data.append(data.ix[timestamp])
        return new_data


def date_range_generate(start,end):
    start_year = int(start.year)
    start_month = int(start.month)
    end_year = int(end.year)
    end_month = int(end.month)
    dates = [datetime.datetime(year=start_year, month=month, day=1) for month in range(start_month, 13)]
    for year in range(start_year+1, end_year+1):
        dates += [datetime.datetime(year=year, month=month, day=1) for month in range(1,13)]
    return dates


def interpolate(series):
    date_list = list(series.index)
    date_list.sort()
    dates = date_range_generate(date_list[0], date_list[-1])
    for date in dates:
        if date not in list(series.index):
            series = series.set_value(date, np.nan)
    series = series.interpolate(method="values")
    to_remove = [elem for elem in list(series.index) if elem.day != 1]
    series.drop(to_remove, inplace=True)
    return series


def check_for_singular(data, to_predict):
    if to_predict == "number_attendees":
        if len(set([data.ix[index]["number_attendees"] for index in data.index])) == 1:
            return True
        else:
            return False
    else:
        if len(set([data.ix[index]["number_applications"] for index in data.index])) == 1:
            return True
        else:
            return False


def trend_predict(data, to_predict):
    print("inside of trend predict")
    cleaned_data = clean_data(data, to_predict)
    print("finished cleaning data")
    if check_for_singular(cleaned_data, to_predict):
        return None
    print("checked for singularity")
    # seasonal decompose
    data = data.dropna()
    if to_predict == "number_attendees":
        if len(data) > 52:
            trend = sm.tsa.seasonal_decompose(data["number_attendees"], freq=52).trend
        elif len(data) > 12:
            trend = sm.tsa.seasonal_decompose(data["number_attendees"], freq=12).trend
        else:
            return None
    else:
        if len(data) > 52:
            trend = sm.tsa.seasonal_decompose(data["number_applications"], freq=52).trend
        elif len(data) > 12:
            trend = sm.tsa.seasonal_decompose(data["number_applications"], freq=12).trend
        else:
            return None
    print("finished creating trend")
    trend = trend.fillna(0)
    trend = trend.iloc[trend.nonzero()[0]]
    s = cleaned_data.T.squeeze()
    s.sort_index(inplace=True)
    print("sorted index by date")
    # clearing out NaNs
    new_data = s.fillna(0)
    new_data = new_data.iloc[new_data.nonzero()[0]]
    interpolated_data = interpolate(new_data.copy())
    print("interpolated data")
    interpolated_data = remove_extreme_values(interpolated_data)
    print("removed extreme data")
    model_order = brute_search(interpolated_data)
    if model_order is  None:
        return None
    else:
        model_order = list(model_order)
    print("model order decided")
    model_order = tuple([int(elem) for elem in model_order])
    #model_order = (1,0,0)
    model = sm.tsa.ARIMA(interpolated_data, model_order).fit(disp=0)
    print("fit model")
    forecast = model.forecast(steps=60)
    print("forecasted future")
    tmp_date = interpolated_data.index[-1]
    end_date = datetime.datetime(year=tmp_date.year+5, month=tmp_date.month, day= tmp_date.day)
    date_range = date_range_generate(interpolated_data.index[-1], end_date)
    print("leaving trend predict")
    return date_range, forecast, trend


def is_nan(obj):
    if type(obj) == type(float()):
        return math.isnan(obj)
    else:
        return False


async def make_prediction(location, to_predict):
    """
    choices for to_predict are "number_attendees" or "number_applications"
    """
    event_objects = EventInformation.query.filter_by(location=location).all()
    if len(event_objects) < 12: #there isn't enough data for a prediction in this case
        return
    print("completed lookup")
    df = pd.DataFrame()
    for event_object in event_objects:
        if to_predict == "number_attendees":
            df = df.append({
                "Date": event_object.timestamp,
                "number_attendees":float(event_object.number_attendees)
            }, ignore_index=True)
        else:
            df = df.append({
                "Date": event_object.timestamp,
                "number_applications":float(event_object.number_applications)
            }, ignore_index=True)
    # sanity checking this is a datetime
    print("created dataframe")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    df.sort_index(inplace=True)
    print("completed dataframe sorting")
    result = trend_predict(df, to_predict)
    print("finished prediction")
    if result:
        date_range, forecast, trend = result
    else:
        return
    print("got result")
    for i in range(len(forecast[0])):
        predicted = Prediction(
            location=location,
            lower_bound=forecast[2][i][0],
            prediction=forecast[0][i],
            upper_bound=forecast[2][i][1],
            timestamp=date_range[i],
            prediction_type=to_predict
        )
        
        db.session.add(predicted)
        db.session.commit()
        print("saved fitted values")
        print("finished Fitted values")
        for ind in range(len(trend)):
            trend_elem = Trend(
                location=location,
                data=trend[ind],
                timestamp=trend.index[ind],
                data_type=to_predict
            )
            db.session.add(trend_elem)
            db.session.commit()
        print("Saved trend results")


def main():
    elements_to_predict = ["number_attendees", "number_applications"]
    for to_predict in elements_to_predict:
        locations = [i for i in EventInformation.query.all() if i.location]
        locations = set([i.location for i in locations])
        loop = asyncio.get_event_loop()
        for index, location in enumerate(locations):
            loop.run_until_complete(make_prediction(location, to_predict))
        loop.close()
