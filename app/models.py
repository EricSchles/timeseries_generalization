"""

Here the models for our database is defined.

I am using Postgres, Flask-SQLAlchemy for this application.

For an introduction to Flask-SQLAlchemy check out: http://flask-sqlalchemy.pocoo.org/2.1/
""" 
from app import db
from datetime import datetime

class EventInformation(db.Model):
    """
    This model gives us an understanding of event information
    
    parameters:
    @timestamp - the date of the event
    @number_attendees - number of people attending the event
    @number_applications - number of applications created during the event
    @location - where the event took place
    """
    __tablename__ = 'event_information'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    number_attendees = db.Column(db.Integer)
    number_applications = db.Column(db.Integer)
    location = db.Column(db.String)
    
    def __init__(self, timestamp=datetime.now(), number_attendees=0, number_applications=0, location=''):
        self.timestamp = timestamp
        self.number_attendees = number_attendees
        self.number_applications = number_applications
        self.location = location
        

class Prediction(db.Model):
    """
    This model gives us an understanding of event information
    
    parameters:
    @timestamp - the date of the event
    @prediction_type - what the prediction refers to, in this case, number of attendees or number of applications
    @prediction - prediction
    @lower_bound - lower_bound
    @upper_bound - upper_bound
    @location - where the event took place
    """
    __tablename__ = 'prediction'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    prediction_type = db.Column(db.String)
    prediction = db.Column(db.Integer)
    lower_bound = db.Column(db.Integer)
    upper_bound = db.Column(db.Integer)
    location = db.Column(db.String)
    
    def __init__(self, prediction_type='', timestamp=datetime.now(), prediction=0, lower_bound=0, upper_bound=0, location=''):
        self.timestamp = timestamp
        self.prediction_type = prediction_type
        self.prediction = prediction
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.location = location


class Trend(db.Model):
    """
    This model gives us an understanding of event information
    
    parameters:
    @timestamp - the date of the event
    @data_type - what the trend refers to, in this case, number of attendees or number of applications
    @data - trend of the data
    @location - where the event took place
    """
    __tablename__ = 'trend'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    data_type = db.Column(db.String)
    data = db.Column(db.Integer)
    location = db.Column(db.String)
    
    def __init__(self, data_type='', timestamp=datetime.now(), data=0, location=''):
        self.timestamp = timestamp
        self.data_type = data_type
        self.data = data
        self.location = location
