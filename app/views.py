from app import app
from app import db
from flask import render_template,request
from app.models import *
from app.timeseries_analysis import main
import json
from app.ingest_data import ingest
from app.prediction import main


def prepare_data_for_plotting(event_info, prediction, trend, to_predict):
    data_object = []
    date_lookup = {}
    if to_predict == "number_attendees":
        prediction = [elem for elem in prediction if elem.prediction_type=="number_attendees"]
        trend = [elem for elem in trend if elem.data_type=="number_attendees"]
        for index,event in enumerate(event_info):
            tmp = {}
            timestamp = str(event.timestamp)
            timestamp = timestamp.split(" ")[0]
            tmp["date"] = timestamp
            date_lookup[timestamp] = index
            tmp["observed"] = float(event.number_attendees)
            data_object.append(tmp)
        for ind,value in enumerate(prediction):
            tmp = {}
            timestamp = str(value.timestamp)
            timestamp = timestamp.split(" ")[0]
            if timestamp in date_lookup.keys():
                data_object[date_lookup[timestamp]]["fitted"] = float(value.prediction)
                data_object[date_lookup[timestamp]]["lower_bound"] = float(value.lower_bound)
                data_object[date_lookup[timestamp]]["upper_bound"] = float(value.upper_bound)
            else:
                tmp["date"] = timestamp
                tmp["fitted"] = float(value.prediction)
                tmp["lower_bound"] = float(value.lower_bound)
                tmp["upper_bound"] = float(value.upper_bound)
                data_object.append(tmp)

        for ind,value in enumerate(trend):
            tmp = {}
            timestamp = str(value.timestamp)
            timestamp = timestamp.split(" ")[0]
            if timestamp in date_lookup.keys():
                data_object[date_lookup[timestamp]]["trend"] = float(value.data)
            else:
                tmp["date"] = timestamp
                tmp["trend"] = float(value.data)
                data_object.append(tmp)
    else:
        prediction = [elem for elem in prediction if elem.prediction_type=="number_applications"]
        trend = [elem for elem in trend if elem.data_type=="number_applications"]
        for index,event in enumerate(event_info):
            tmp = {}
            timestamp = str(event.timestamp)
            timestamp = timestamp.split(" ")[0]
            tmp["date"] = timestamp
            date_lookup[timestamp] = index
            tmp["observed"] = float(event.number_applications)
            data_object.append(tmp)
        for ind,value in enumerate(prediction):
            tmp = {}
            timestamp = str(value.timestamp)
            timestamp = timestamp.split(" ")[0]
            if timestamp in date_lookup.keys():
                data_object[date_lookup[timestamp]]["fitted"] = float(value.prediction)
                data_object[date_lookup[timestamp]]["lower_bound"] = float(value.lower_bound)
                data_object[date_lookup[timestamp]]["upper_bound"] = float(value.upper_bound)
            else:
                tmp["date"] = timestamp
                tmp["fitted"] = float(value.prediction)
                tmp["lower_bound"] = float(value.lower_bound)
                tmp["upper_bound"] = float(value.upper_bound)
                data_object.append(tmp)

        for ind,value in enumerate(trend):
            tmp = {}
            timestamp = str(value.timestamp)
            timestamp = timestamp.split(" ")[0]
            if timestamp in date_lookup.keys():
                data_object[date_lookup[timestamp]]["trend"] = float(value.data)
            else:
                tmp["date"] = timestamp
                tmp["trend"] = float(value.data)
                data_object.append(tmp)
    return json.dumps(data_object)


@app.route("/", methods=["GET","POST"])
def index():
    if request.method=="POST":
        location = request.form.get("location")
        to_predict = request.form.get("to_predict")
        # Getting the data by location
        event_info = EventInformation.query.filter_by(location=location).all()
        prediction = Prediction.query.filter_by(location=location).all()
        trend = Trend.query.filter_by(location=location).all()
        data_object = prepare_data_for_plotting(event_info, prediction, trend, to_predict)
        return render_template("index.html",data_object=data_object,header=location,data_type=" ".join(to_predict.split("_")))
    else:
        events = EventInformation.query.all()
        locations = list(set([event.location for event in events]))
        return render_template("index.html",locations=locations, data_object=json.dumps({}))

    
@app.route("/ingest_data",methods=["GET","POST"])
def ingest_data():
    #saving file locally goes here
    csv_file = "nac_events_Y5_fortimeseries.csv"
    ingest("data/"+csv_file)
    return "success"

