#!/bin/sh

AM_USERNAME=username_here
AM_PASSWORD=password_here
PW_HOUSE_ID=house_id_here
PW_API_KEY=api_key_here
AM_DEVICE_NAME=device_name_here
START=$(date -u --date='1 hour ago' +"%Y-%m-%dT%H:00:00Z")
END=$(date -u +"%Y-%m-%dT%H:00:00Z")

PYTHONPATH=~/plotwatt-api/ python ~/alertme2plotwatt/alertme.py --AM_USERNAME=$AM_USERNAME --AM_PASSWORD=$AM_PASSWORD --PW_HOUSE_ID=$PW_HOUSE_ID --PW_API_KEY=$PW_API_KEY --START=$START --END=$END --AM_DEVICE_NAME=$AM_DEVICE_NAME
