# -*- coding: utf-8 -*-
"""
Created on Tue Feb 12 00:05:33 2019

@author: jawhite
"""
#matplotlib inline
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, inspect
from flask import Flask, jsonify


import numpy as np
import pandas as pd

import datetime as dt


# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

engine = create_engine("sqlite:///Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)



# We can view all of the classes that automap found
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


# Create our session (link) from Python to the DB
session = Session(engine)


# Design a query to retrieve the last 12 months of precipitation data and plot the results

# Perform a query to retrieve the data and precipitation scores
station_list = session.query(Measurement)
max_date=''
x=0
for m in station_list:
    if x==0:
        max_date=m.date
        x+=1
    else:
        if max_date<=m.date:
            max_date=m.date
        x+=1
# Calculate the date 1 year ago from the last data point in the database
n_datetime = dt.datetime(int(max_date[0:4])-1, int(max_date[5:7]),int(max_date[8:]))
                                     
#help with temperature obs
new_stat_list_2=session.query(Measurement.date,Measurement.tobs).filter(Measurement.date>=n_datetime)
df_temp = pd.DataFrame(new_stat_list_2[:-1], columns=['Date','Temperature'])
df_temp.set_index('Date', inplace=True, )

new_stat_list=session.query(Measurement.date,Measurement.prcp).filter(Measurement.date>=n_datetime)


# Save the query results as a Pandas DataFrame and set the index to the date column
df = pd.DataFrame(new_stat_list[:-1], columns=['Date','Precipitation'])
df.set_index('Date', inplace=True, )


# Sort the dataframe by date
df=df.sort_values(by=['Date'])

df_1=df.groupby(['Date']).sum()


# Design a query to show how many stations are available in this dataset?
results = session.query(Measurement,Measurement.station).\
    group_by(Measurement.station).count()

results_1 = session.query(Measurement)

station_list=[]
station_count=[]

for r in results_1:
    if r.station in station_list:
        station_count[station_list.index(r.station)]+=1
    else:
        station_list.append(r.station)
        station_count.append(1)

l_lists=[]

for x in range(len(station_list)):
    l_lists.append([station_list[x],station_count[x]])

l_df=pd.DataFrame(l_lists,columns=["Stations","Count"])

l_df=l_df.sort_values(by="Count",ascending=False)
final_list=list(l_df.itertuples(index=False, name=None))


# Using the station id from the previous query, calculate the lowest temperature recorded, 
# highest temperature recorded, and average temperature most active station?
active_station=final_list[0][0]

obs=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter_by(station=active_station)
final_obs=session.query(Measurement.tobs).filter_by(station=active_station).filter(Measurement.date>=n_datetime)
final_df = pd.DataFrame(final_obs[:-1], columns=['Temperature'])
    


# beginning of Creating the API end points
app = Flask(__name__)

#################################################
# Flask Routes
#################################################


@app.route("/")
def index():
   return (
        f"Welcome to Jimmy's HW API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<'start'> OR /api/v1.0/<'start'>/<'end'><br/>"

    )
@app.route("/api/v1.0/precipitation")
def precipitation():
    #Return the precipitation data#
    df_dict=df_1.to_dict()
    return jsonify(df_dict['Precipitation'])

@app.route("/api/v1.0/stations")
def stations():
    #Return the stations data
    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def tobs():
    #Return the temperature data
    temp_dict=df_temp.to_dict()
    return jsonify(temp_dict)

@app.route("/api/v1.0/<start>")
def start(start):
    #return the date from a start date
    session=Session(engine)
    start_help=dt.datetime(int(start[0:4]), int(start[5:7]),int(start[8:]))
    start_obs=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date>=start_help)
    return(jsonify({"Minimum Temperature":start_obs[0][0],"Maximum Temperature":start_obs[0][1],"Average Temperature":start_obs[0][2]}))

@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    session=Session(engine)
    start_help=dt.datetime(int(start[0:4]), int(start[5:7]),int(start[8:]))
    end_help=dt.datetime(int(end[0:4]), int(end[5:7]),int(end[8:]))
    start_end_obs=session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date>=start_help).filter(Measurement.date<=end_help)
    return(jsonify({"Minimum Temperature":start_end_obs[0][1],"Maximum Temperature":start_end_obs[0][1],"Average Temperature":start_end_obs[0][2]}))



# Stopping flask can be a pain, so I recommend this ONLY in dev... not production
from flask import request

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    
@app.route('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

if __name__ == "__main__":
    app.run(debug=True)