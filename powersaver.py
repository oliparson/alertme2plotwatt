from alertme import *

def query_channel_value(username, hub_id, device_type, device_id, channel):
    theurl = API_URL + 'users/' + username + '/hubs/' + hub_id + '/devices/' + device_type + "/" + device_id + '/channels/' + channel
    
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
        return query_channel_value(username, hub_id, device_type, device_id, channel)
    
def put_device_relay(username, hub_id, device_type, device_id, state):
    theurl = API_URL + 'users/' + username + '/hubs/' + hub_id + '/devices/' + 'SmartPlugs/' + device_id + '/relay'
    thedata = 'state='+state
    
    try:
        req = Request(theurl, data=thedata)
        req.add_header('Content-Type', 'your/contenttype')
        req.get_method = lambda: 'PUT'
        handle = opener.open(req)
        
        read = handle.read()
        
        #result = json.loads(read)
        #print " " + channel + " data: " + read
        return read
    except urllib2.HTTPError, e:
        # 404 error when data does not exist, don't retry
        print 'AlertMe API HTTPError:',e
        return False
    except urllib2.URLError, e:
        # connection problem, retry
        print 'AlertMe API URLError:',e
        return query_channel_value(username, hub_id, device_type, device_id, channel)

def powersave(AM_USERNAME, AM_PASSWORD, AM_DEVICE_TO_MONITOR, AM_DEVICE_TO_POWERSAVE):
    DEVICE_CHANNELS = ['power']
    THRESHOLD = 200
    
    log_in_json = log_in(AM_USERNAME, AM_PASSWORD)
    if not log_in_json:
        print 'bad AlertMe credentials'
    else:
        hub_id = str(log_in_json['hubIds'][0])
        hub_devices = query_hub_devices(AM_USERNAME, hub_id)
        recent_power = None
        
        for device in hub_devices:
            device_name = device['name']
            device_type = device['type']
            device_id = device['id']
            if device_name == AM_DEVICE_TO_MONITOR:
                print device_name, device_type, device_id
                device_channels = query_devices_channels(AM_USERNAME, hub_id, device_type, device_id)
                for channel in device_channels:
                    channel_name = channel['name']
                    if channel_name in DEVICE_CHANNELS:
                        ret = query_channel_value(AM_USERNAME, hub_id, device_type, device_id, channel_name)
                        recent_power = ret['value']
                        
        if recent_power:
            if recent_power >= THRESHOLD:
                turn_device = 'on'
            else:
                turn_device = 'off'
                
            print 'recent_power', recent_power, 'THRESHOLD', THRESHOLD, 'turning_device', turn_device
             
            for device in hub_devices:
                device_name = device['name']
                device_type = device['type']
                device_id = device['id']
                if device_type == 'SmartPlug' and device_name == AM_DEVICE_TO_POWERSAVE:
                    print put_device_relay(AM_USERNAME, hub_id, device_type, device_id, turn_device)

if __name__ == "__main__":

    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-u", "--AM_USERNAME", dest="AM_USERNAME",
                      help="Username of AlertMe account")
    parser.add_option("-p", "--AM_PASSWORD", dest="AM_PASSWORD",
                      help="Password of AlertMe account")
    parser.add_option("-m", "--AM_DEVICE_TO_MONITOR", dest="AM_DEVICE_TO_MONITOR",
                      help="Device name of AlertMe device to read current value")
    parser.add_option("-s", "--AM_DEVICE_TO_POWERSAVE", dest="AM_DEVICE_TO_POWERSAVE",
                      help="Device name of AlertMe device to powersave")
    
    (options, args) = parser.parse_args()
    print options
    
    powersave(options.AM_USERNAME, 
             options.AM_PASSWORD, 
             options.AM_DEVICE_TO_MONITOR, 
             options.AM_DEVICE_TO_POWERSAVE)
    