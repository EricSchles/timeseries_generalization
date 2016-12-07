import pandas as pd
import os
import math
import json
import datetime
import time
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import brute
import statistics
from functools import partial

# A bit about this file - Python is a great language full of lots of useful data science libraries.  But it's not that fast.  For this reason we use a series of functions which send data to json files, which can be used by the language as Python Dictionaries.  Because of the size of the data, big but not *that* big, it made sense to chop up the tasks and not repeat computation unless necessary.  Otherwise debugging and iteration would be difficult, because just processing the data, takes a while.

# Therefore we have the following methods:

# making_categories - which maps individual labor categories into buckets across three fields - education level, years of experience and schedule.

# I don't really undetstand what a schedule is, but it's kind of like a geographic region?  As well as a business line / set of skills.  So, if you are a schedule 70, it's likely you're in IT and it's even more likely you're a software developer.  It's worth stating that there is talk of moving over to SIN numbers which are used by the government to do something similar to the schedule, but at a more granular level.  Sometimes these SIN numbers have semantic data attached.  And sometimes, they do not.  So it's best to think of them as unique identifiers.  For this reason, it might be worth it to update this script down the road to work off of SIN numbers.  But for right now schedule seems like the right call.

#helpful resource: https://www.analyticsvidhya.com/blog/2016/02/time-series-forecasting-codes-python/

def is_nan(obj):
    if isinstance(obj,float):
        return math.isnan(obj)
    else:
        return False

def date_to_datetime(time_string):
    return datetime.datetime.strptime(time_string, '%m/%d/%Y')

def total_error(values,fitted_values):
    if (len(values) == len(fitted_values)) or (len(values) < len(fitted_values)):
        return sum([abs(values[ind] - fitted_values[ind]) for ind in range(len(values))]) 
    else:
        return sum([abs(values[ind] - fitted_values[ind]) for ind in range(len(fitted_values))])

def ave_error(values,fitted_values):
    if (len(values) == len(fitted_values)) or (len(values) < len(fitted_values)):
        return sum([abs(values[ind] - fitted_values[ind]) for ind in range(len(values))])/len(values) 
    else:
        return sum([abs(values[ind] - fitted_values[ind]) for ind in range(len(fitted_values))])/len(values)
    
def check_for_extreme_values(sequence,sequence_to_check=None):
    mean = statistics.mean(sequence)
    stdev = statistics.stdev(sequence)
    if sequence_to_check != None:
        for val in sequence_to_check:
            if val >= mean + (stdev*2):
                sequence_to_check.remove(val)
            elif val <= mean - (stdev*2):
                sequence_to_check.remove(val)
        return sequence_to_check
    else:
        for val in sequence:
            if val >= mean + (stdev*2):
                sequence.remove(val)
            elif val <= mean - (stdev*2):
                sequence.remove(val)
        return sequence
        
def setting_y_axis_intercept(data,model):
    data = list(data["Year 1/base"])
    fittedvalues = list(model.fittedvalues)
    avg = statistics.mean(data)
    median = statistics.median(data)
    possible_fitted_values = []

    possible_fitted_values.append([elem + avg for elem in fittedvalues])
    possible_fitted_values.append([elem + data[0] for elem in fittedvalues])
    possible_fitted_values.append([elem + median for elem in fittedvalues])
    possible_fitted_values.append(fittedvalues)
    min_error = 1000000
    best_fitted_values = 0
    for ind,f_values in enumerate(possible_fitted_values):
        cur_error = total_error(data,f_values)
        avg_error = ave_error(data,f_values)
        if avg_error < min_error:
            min_error = avg_error 
            best_fitted_values = ind
    print("minimum error:",min_error)
    return possible_fitted_values[best_fitted_values]

#this comes from here: http://stackoverflow.com/questions/22770352/auto-arima-equivalent-for-python
def objective_function(data,order):
    return sm.tsa.ARIMA(data,order).fit().aic

def model_search(data):
    obj_func = partial(objective_function,data)
    upper_bound_AR = 10
    upper_bound_I = 10
    upper_bound_MA = 10
    grid_not_found = True
    while grid_not_found:
        try:
            if upper_bound_AR < 0 or upper_bound_I < 0 or upper_bound_MA < 0:
                grid_not_found = False
            grid = (slice(1,upper_bound_AR,1),slice(1,upper_bound_I,1),slice(1,upper_bound_MA,1))
            return brute(obj_func, grid, finish=None)
        except Exception as e: #found here: http://stackoverflow.com/questions/4308182/getting-the-exception-value-in-python
            error_string = str(e)
            if "MA" in error_string:
                upper_bound_MA -= 1
            elif "AR" in error_string:
                upper_bound_AR -= 1
            else:
                upper_bound_I -= 1
                
    #assuming we don't ever hit a reasonable set of upper_bounds, it's pretty safe to assume this will work
    try:
        grid = (slice(1,2,1),slice(1,2,1),slice(1,2,1))
        return brute(obj_func, grid, finish=None)
    except: #however we don't always meet invertibility conditions
        #Here we explicitly test for a single MA or AR process being a better fit
        #If either has a lower (better) aic score we return that model order
        model_ar_one = sm.tsa.ARIMA(data,(1,0,0)).fit()
        model_ma_one = sm.tsa.ARIMA(data,(0,0,1)).fit()
        if model_ar_one.aic < model_ma_one.aic:
            return (1,0,0)
        else:
            return (0,0,1)
    
def trend_predict(data):
    #seasonal decompose 
    if len(data) > 52:
        s = sm.tsa.seasonal_decompose(data["Year 1/base"],freq=52)
    elif len(data) > 12:
        s = sm.tsa.seasonal_decompose(data["Year 1/base"], freq=12)
    else:
        return None
    #clearing out NaNs
    new_data = s.trend.fillna(0)
    new_data = new_data.iloc[new_data.nonzero()[0]]
    model_order = list(model_search(data))
    model_order = tuple([int(elem) for elem in model_order])
    model = sm.tsa.ARIMA(new_data,model_order).fit()
    model.fittedvalues = setting_y_axis_intercept(new_data,model)
    return model


if __name__ == '__main__':

    try:
        #for key in keys:
        data = pd.DataFrame() 
        
        #http://stackoverflow.com/questions/34494780/time-series-analysis-unevenly-spaced-measures-pandas-statsmodels
        #http://stackoverflow.com/questions/34457281/decomposing-trend-seasonal-and-residual-time-series-elements
           
        model = trend_predict(data)
        #model.fittedvalues = setting_y_axis_intercept(data,model)
        
        plt.plot(data)
        plt.plot(model.fittedvalues, color='red')
        plt.show()
    except:
        import code
        code.interact(local=locals())

