from datetime import datetime
import pandas as pd
from functools import partial
import statsmodels.api as sm
from scipy.optimize import brute
import random

def objective_function(data, order):
    return sm.tsa.ARIMA(data, order).fit().aic


def brute_search(data):
    obj_func = partial(objective_function, data)
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
            return brute(obj_func, grid, finish=None)
        except Exception as e:
            error_string = str(e)
            if "MA" in error_string:
                upper_bound_MA -= 1
            elif "AR" in error_string:
                upper_bound_AR -= 1
            else:
                upper_bound_I -= 1
    try:
        grid = (slice(1,2,1), slice(1,2,1), slice(1,2,1))
        return brute(obj_func, grid, finish=None)
    except:
        model_ar_one = sm.tsa.ARIMA(data, (1, 0, 0)).fit()
        model_ma_one = sm.tsa.ARIMA(data, (0, 0, 1)).fit()
        if model_ar_one.aic < model_ma_one.aic:
            return (1, 0, 0)
        else:
            return (0, 0, 1)


def main(filename):
    df = pd.read_csv(filename)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    del df["Location"]
    del df["N_applications"]
    del df["Date"]
    df.sort_index(inplace=True)
    model_order = brute_search(df)
    model_order = tuple([int(elem) for elem in model_order])
    model = sm.tsa.ARIMA(df, model_order).fit()
    forecast = model.forecast(steps=10)

