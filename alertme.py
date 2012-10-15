import time
import datetime
from datetime import datetime as datetime2
from datetime import timedelta
import urllib
import urllib2
import cookielib
import json
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

# AlertMe API settings
DOWNLOAD_INTERVAL = 3600 # 1 hour
DEVICE_CHANNELS = {
                   'MeterReader' : ['power'],
                   'Lamp' : [],
                   'Button' : [],
                   'Keyfob' : [],
                   'MotionSensor' : [],
                   'ContactSensor' : [],
                   'SmartPlug' : [],
                   }
OPERATION = 'average'

def transfer(AM_USERNAME, AM_PASSWORD, PW_HOUSE_ID, PW_API_KEY, START_TIME, END_TIME, AM_DEVICE_NAME=None, PW_METER_ID=None):
    '''
    START_TIME - timestamp string in ISO8601
    END_TIME - timestamp string in ISO8601
    AM_DEVICE_NAME - AlertMe device name string, required if multiple MeterReaders devices exist
    PW_METER_ID - PlotWatt meter id int, required if multiple meters exist
    '''
    
    # parse start and end times
    utc_format = '%Y-%m-%dT%H:%M:%SZ'
    try:
        start = datetime2.strptime(START_TIME, utc_format)
        end = datetime2.strptime(END_TIME, utc_format)
    except ValueError, e:
        print 'start or end time not in ',utc_format,'format'
        return -1
    
    # PlotWatt API
    pw = Plotwatt(PW_HOUSE_ID, PW_API_KEY)
    try:
        pw.list_meters()
    except urllib2.HTTPError, e:
        print 'bad PlotWatt credentials'
        return -1
    if not PW_METER_ID:
        print 'PlotWatt meter not specified'
        pw_meter_list = pw.list_meters()
        if len(pw_meter_list) == 0:
            print 'No PlotWatt meters found. Creating meter'
            pw_meter_list = pw.create_meters(1)
        PW_METER_ID = pw_meter_list[0]
        print 'Using PlotWatt meter ', PW_METER_ID

    # AlertMe API
    log_in_json = log_in(AM_USERNAME, AM_PASSWORD)
    if not log_in_json:
        print 'bad AlertMe credentials'
        return -1
    hub_id = str(log_in_json['hubIds'][0])
    hub_devices = query_hub_devices(AM_USERNAME, hub_id)
    for device in hub_devices:
        device_name = device['name']
        device_type = device['type']
        device_id = device['id']
        if device_type in DEVICE_CHANNELS.keys() and ((not AM_DEVICE_NAME) or device_name == AM_DEVICE_NAME):
            device_channels = query_devices_channels(AM_USERNAME, hub_id, device_type, device_id)
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
			
            # loop over hour long intervals downloading and uploading data
			period = (int(time.mktime(end.timetuple()))-int(time.mktime(start.timetuple())))
			for i in range(period/DOWNLOAD_INTERVAL):
			    temp_start = start + timedelta(seconds=i*DOWNLOAD_INTERVAL)
			    temp_end = start + timedelta(seconds=(i+1)*DOWNLOAD_INTERVAL-1)
			    start_string = str(int(time.mktime(temp_start.timetuple())))
			    end_string = str(int(time.mktime(temp_end.timetuple())))
			    print str(datetime2.now()),':',str(temp_start),'->',str(temp_end)
			    historical_values = query_channel_data(AM_USERNAME, hub_id, device_type, device_id, channel_name, start_string, end_string, INTERVAL, OPERATION)
			    if historical_values:
    				timestamps,data = parse_json(historical_values)
    				push_readings_to_pw(pw, PW_METER_ID,data,timestamps)

if __name__ == "__main__":

    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-u", "--AM_USERNAME", dest="AM_USERNAME",
                      help="Username of AlertMe account")
    parser.add_option("-p", "--AM_PASSWORD", dest="AM_PASSWORD",
                      help="Password of AlertMe account")
    parser.add_option("-i", "--PW_HOUSE_ID", dest="PW_HOUSE_ID",
                      help="House ID of PlotWatt account")
    parser.add_option("-k", "--PW_API_KEY", dest="PW_API_KEY",
                      help="API key of PlotWatt account")
    parser.add_option("", "--START", dest="START",
                      help="API key of PlotWatt account")
    parser.add_option("", "--END", dest="END",
                      help="API key of PlotWatt account")
    parser.add_option("", "--AM_DEVICE_NAME", dest="AM_DEVICE_NAME",
                      help="Name of MeterReader of AlertMe account")
    parser.add_option("", "--PW_METER_ID", dest="PW_METER_ID",
                      help="API key of PlotWatt account")
    
    (options, args) = parser.parse_args()
    print options
    
    transfer(options.AM_USERNAME, 
             options.AM_PASSWORD, 
             options.PW_HOUSE_ID, 
             options.PW_API_KEY, 
             options.START, 
             options.END, 
             AM_DEVICE_NAME=options.AM_DEVICE_NAME,
             PW_METER_ID=options.PW_METER_ID)
