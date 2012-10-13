alertme2plotwatt
================

Python library for pushing electricity data from an AlertMe account to a PlotWatt account

This repository contains one python module, alertme.py, whose transfer function downloads data from an AlertMe account and uploads it to a PlotWatt account.


The transfer function has has six required parameters:

AM_USERNAME - the username of the AlertMe account to download data from

AM_PASSWORD - the password of the AlertMe account to download data from

PW_HOUSE_ID - the house id of the PlotWatt account to upload data to, available here after logging in https://plotwatt.com/docs/api

PW_API_KEY - the API key of the PlotWatt account to upload data to, available here after logging in https://plotwatt.com/docs/api

START - timestamp of the start of the interval in the format YYYY-mm-ddTHH:MM:SSZ (inclusive)

END - timestamp of the end of the interval in the format YYYY-mm-ddTHH:MM:SSZ (exclusive)


and two optional parameters:

AM_DEVICE_NAME - required if the AlertMe account has more than one MeterReader

PW_METER_ID - required it the PlotWatt account has more than one meter


The script will first print to the standard output some JSON as returned by the AlertMe API while logging in.
This is then followed by two timestamps of the form START -> END, for each hour of data transferred.

Running on a VM on my laptop, this takes about 30 minutes to transfer a month of data at 1 second resolution.
I think most of the time is spent waiting for a response from the AlertMe API, although I haven't profiled this

