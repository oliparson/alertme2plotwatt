import time
import datetime
from datetime import datetime as datetime2
from datetime import timedelta
import urllib
import urllib2
import cookielib
import json
#import matplotlib.pyplot as plt
from plotwattapi import Plotwatt
import numpy as np

API_URL = 'https://api.alertme.com/v5/'
COOKIEFILE = 'cookies.lwp'

cj = cookielib.LWPCookieJar()
urlopen = urllib2.urlopen
Request = urllib2.Request

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)

def log_in(username, password):
    theurl = API_URL + 'login'
    txdata = urllib.urlencode({"username" : username, "password" : password})
    
    try:
        req = Request(theurl, txdata)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        print "login: " + read
        
        if cj is None:
            print "no cookies"
        else:
            cj.save(COOKIEFILE)
        return result
    
    except urllib2.HTTPError, he:
        print 'exception from request: ', theurl, he
        return False

def query_user_info(username):
    theurl = API_URL + 'users/' + username
    
    try:
        req = Request(theurl)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        print "user info: " + read
        return result
    
    except urllib2.HTTPError, he:
        print 'exception from request: ', theurl, he
        return False

def query_hub(username):
    theurl = API_URL + 'users/' + username + '/hubs'
    
    try:
        req = Request(theurl)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        print "user hubs: " + read
        return result
    
    except urllib2.HTTPError, he:
        print 'exception from request: ', theurl, he
        return False
    
def query_hub_info(username, hub_id):
    theurl = API_URL + 'users/' + username + '/hubs/' + hub_id
    
    try:
        req = Request(theurl)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        print "hub info: " + read
        return result
    
    except urllib2.HTTPError, he:
        print 'exception from request: ', theurl, he
        return False

def query_hub_devices(username, hub_id):
    theurl = API_URL + 'users/' + username + '/hubs/' + hub_id + '/devices'
    
    try:
        req = Request(theurl)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        print "hub devices: " + read
        return result
    
    except urllib2.HTTPError, he:
        print 'exception from request: ', theurl, he
        return False
    
def query_devices_channels(username, hub_id, device_type, device_id):
    theurl = API_URL + 'users/' + username + '/hubs/' + hub_id + '/devices/' + device_type + "/" + device_id + '/channels'
    
    try:
        req = Request(theurl)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        print device_type + " channels: " + read
        return result
    
    except urllib2.HTTPError, he:
        print 'exception from request: ', theurl, he
        return False
    
def query_channel_data(username, hub_id, device_type, device_id, channel, start, end, interval, operation):
    theurl = API_URL + 'users/' + username + '/hubs/' + hub_id + '/devices/' + device_type + "/" + device_id + '/channels/' + channel
    theurl = theurl + '?start=' + start + '&end=' + end +'&interval=' + interval + '&operation=' + operation
    
    try:
        req = Request(theurl)
        handle = urlopen(req)
        read = handle.read()
        result = json.loads(read)
        #print " " + channel + " data: " + read
        return result
    except urllib2.HTTPError, e:
        # 404 error when data does not exist, don't retry
        print 'AlertMe API HTTPError:',e
        return False
    except urllib2.URLError, e:
        # connection problem, retry
        print 'AlertMe API URLError:',e
        return query_channel_data(username, hub_id, device_type, device_id, channel, start, end, interval, operation)
    
def write_json_to_csv(json, file):
    start = json['start']
    interval = json['interval']
    data = json['values']['average']
    for i in range(len(data)):
        timestamp = start + i*interval
        data_item = data[i]
        csv_line = str(timestamp) + ', ' + str(data_item) + '\n'
        file.write(csv_line)
        
def write_to_file(timestamps, data, file):
    string = ''
    for pair in zip(timestamps,data):
        string += str(pair[0])+','+str(pair[1])+'\n'
    file.write(string)
        
def parse_json(json):
    start = json['start']
    interval = json['interval']
    data = np.array(json['values']['average'])
    unix_timestamps = range(start,start+(interval*len(data)),interval)
    timestamps = np.array([datetime2.fromtimestamp(t) for t in unix_timestamps])
    # remove None values 
    none_idx = np.nonzero(np.equal(data, None))[0]
    if len(none_idx) > 0:
        data = np.delete(data, none_idx)
        timestamps = np.delete(timestamps, none_idx)
    # convert from W to kW
    data = data/float(1000)
    
    return timestamps.tolist(), data.tolist()

def push_readings_to_pw(pw,PW_METER_ID,data,timestamps):
    try:
        pw.push_readings(PW_METER_ID,data,timestamps)
    except urllib2.URLError, e:
        print 'PlotWatt API error:',e
        push_readings_to_pw(pw,PW_METER_ID,data,timestamps)

# logging directory
OUTPUT_DIRECTORY = 'energy_data/'

# AlertMe details
USERNAME = ''
PASSWORD = ''
DOWNLOAD_INTERVAL = 3600 # 1 hours
DEVICE_NAMES = ['HouseMeterReader']
DEVICE_CHANNELS = {
                   'MeterReader' : ['power'],
                   'Lamp' : [],
                   'Button' : [],
                   'Keyfob' : [],
                   'MotionSensor' : [],
                   'ContactSensor' : [],
                   'SmartPlug' : [],
                   }
START = datetime2(2012,9,24,0,0,0)
END = datetime2(2012,9,24,01,0,0)
OPERATION = 'average'

# PlotWatt details
PW_HOUSE_ID = ''
PW_API_KEY = ''
PW_METER_ID = ''

def transfer(USERNAME, PASSWORD, PW_HOUSE_ID, PW_API_KEY, PW_METER_ID): 
    pw = Plotwatt(PW_HOUSE_ID, PW_API_KEY)

    log_in_json = log_in(USERNAME, PASSWORD)
    hub_id = str(log_in_json['hubIds'][0])
    hub_devices = query_hub_devices(USERNAME, hub_id)
    for device in hub_devices:
        device_name = device['name']
        device_type = device['type']
        device_id = device['id']
        if device_type in DEVICE_CHANNELS.keys() and device_name in DEVICE_NAMES:
            device_channels = query_devices_channels(USERNAME, hub_id, device_type, device_id)
            for channel in device_channels:
                channel_name = channel['name']
                if channel_name in DEVICE_CHANNELS[device_type]:
                    if channel_name == 'power':
                        if device_type == 'MeterReader':
                            INTERVAL = '1'
                        elif device_type == 'SmartPlug':
                            INTERVAL = '30'
                        else:
                            INTERVAL = '120'
			
			# create a file to log the uploaded data to
			filename = str(START)+' - '+str(END)+'.csv'
			#file = open(OUTPUT_DIRECTORY + filename, 'w')
                
			period = (int(time.mktime(END.timetuple()))-int(time.mktime(START.timetuple())))
			for i in range(period/DOWNLOAD_INTERVAL):
			    temp_start = START + timedelta(seconds=i*DOWNLOAD_INTERVAL)
			    temp_end = START + timedelta(seconds=(i+1)*DOWNLOAD_INTERVAL-1)
			    start_string = str(int(time.mktime(temp_start.timetuple())))
			    end_string = str(int(time.mktime(temp_end.timetuple())))
			    print str(datetime2.now()),':',str(temp_start),'->',str(temp_end)
			    historical_values = query_channel_data(USERNAME, hub_id, device_type, device_id, channel_name, start_string, end_string, INTERVAL, OPERATION)
			    if historical_values:
				timestamps,data = parse_json(historical_values)
				#write_to_file(timestamps,data,file)
				#push_readings_to_pw(pw, PW_METER_ID,data,timestamps)
				#print data
			    
			#file.close()

