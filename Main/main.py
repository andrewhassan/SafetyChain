from BlueRoverWebApi import BlueRoverWebApi
import time
import json
from ftplib import FTP
import sys
import os

POLLING_DURATION = 300;
temperature_events = {}
store_mapping = {}

ftphost = "host"
ftpuser = "user"
ftppass = "password"

apikey = ""
apitoken = ""

folder = "safety_chain_aggregation"

class TemperatureEvent(object):
    """
    This class simply holds an RFID tag number and it's temperature points. It provides a method
    for returning the average temperature of all its points.
    """
    def __init__(self, tagNum, storeId):
        self.tagNum = tagNum
        self.temps = []
        self.storeId = storeId
        
    def add_temperature(self, temp):
        self.temps.append(temp)
        
    def get_average_temp(self):
        total = 0
        for temp in self.temps:
            total += temp
        
        average = total/len(self.temps)
        
        return average
    
    def temp_count(self):
        return len(self.temps) 
    
    def __str__(self):
        result = ", ".join(self.temps)
        return result
    
def directory_exists(ftp, directory):
    filelist = []
    ftp.retrlines('LIST',filelist.append)
    for f in filelist:
        if f.split()[-1] == directory and f.upper().startswith('D'):
            return True
    return False

if __name__ == "__main__":
    # Get command line arguments
    args = sys.argv

    # Remove the first argument
    args.pop(0)

    # Generate the key, value pairs and set the appropriate properties for the arguments
    for arg in sys.argv:
        (k, v) = arg.split("=")
        k = k.lower()
        if k == "ftpuser":
            ftpuser = v
        elif k == "ftppass":
            ftppass = v
        elif k == "ftphost":
            ftphost = v
        elif k == "apikey":
            apikey = v
        elif k == "apitoken":
            apitoken = v
        elif k == "dir":
            folder = v
            
    # Load the store to RFID mappings from the stores.json file
    config = open(os.getcwd() + "/config/stores.json", 'r')
    store_mapping = json.loads("\n".join(config.readlines()))
    config.close()
    
    # Create an API object using the key and tokens given to you
    api = BlueRoverWebApi.Api(apikey, apitoken)
    
    count = 1
    
    # TODO: Add paging (only supports 1 page right now)
    while True:
        startTime = int(time.time())
        
        # Call API
        result = api.call_api("/event", {"start_time": startTime - POLLING_DURATION, "end_time": startTime, "page": 0}, False)
        
        # Convert json string to dict
        parsed_dict = json.loads(result)
        
        # Add the temperatures for each tag into the global dictionary
        for event in parsed_dict['events']:
            tagNum = event['rfidTagNum']
            if (event['rfidTemperature'] == None):
                continue
            if (tagNum in temperature_events):
                temperature_events[tagNum].add_temperature(event['rfidTemperature'])
            else:
                temp_event = TemperatureEvent(tagNum, store_mapping[str(tagNum)])
                temp_event.add_temperature(event['rfidTemperature'])
                temperature_events[tagNum] = temp_event
                
        # Since we want to write to file once every 3 hours, we collect data every 600 seconds 18 times
        if (count < 36):
            count += 1
        # Once we've collected 3 hours of data, we write to file
        else:
            # Generate a CSV file for each store
            store_csv_files = {}
            
            # Group each event by its store and add the data to the appropriate store CSV file
            for event in temperature_events:
                if not temperature_events[event].storeId in store_csv_files:
                    # Add the CSV header
                    store_csv_files[temperature_events[event].storeId] = "Tag Num,Temperature Average\n"
                
                # Add the event data  
                store_csv_files[temperature_events[event].storeId] += str(event) + "," + str(temperature_events[event].get_average_temp()) + "\n"
            
            # Save and upload each store's CSV file
            for store in store_csv_files:
                # Filename ({storeId}_{timestamp}.csv)
                filename = store + "_" + str(int(time.time())) + ".csv"
                
                # Open and write the file
                f = open(filename, 'w')
                f.write(store_csv_files[store])
                f.close()
                
                # Open the file to upload to FTP
                f = open(filename, 'r')
                
                # Open connection to the FTP site
                ftp = FTP(ftphost)
                ftp.login(ftpuser, ftppass)
                
                # Store the file
                if not directory_exists(ftp, folder): # Remove these lines if you want files in the root directory
                    ftp.mkd(folder) # Remove these lines if you want files in the root directory
                ftp.cwd(folder) # Remove these lines if you want files in the root directory
                ftp.storlines("STOR " + filename, f)
                
                # Close connection and file
                ftp.quit()
                f.close()
                
                # Delete the local file
                os.remove(filename)
            
            # Reset the temperature events for a new loop
            temperature_events = {}
            count = 1
        
        # Calculate the drift time for the loop so that the next one starts exactly at 600 seconds
        endTime = int(time.time())
        drift = endTime - startTime
        
        # Sleep
        time.sleep(POLLING_DURATION - drift)
