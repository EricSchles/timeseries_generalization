from app.models import EventInformation
from app import db
import pandas as pd
import math

def is_nan(obj):
    try:
        return math.isnan(obj)
    except:
        return False


def nan_to_zero(obj):
    if is_nan(obj):
        return 0
    else:
        return float(obj)

    
def ingest(filename):
    df = pd.read_csv(filename)
    for index in df.index:
        event_information = EventInformation(
            timestamp=df.ix[index]["Date"],
            number_attendees=nan_to_zero(df.ix[index]["N_attendees"]),
            number_applications=nan_to_zero(df.ix[index]["N_applications"]),
            location=df.ix[index]["Location"]
        )
        db.session.add(event_information)
        db.session.commit()
        
