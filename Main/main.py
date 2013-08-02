from BlueRoverWebApi import BlueRoverWebApi
import time
import json

POLLING_DURATION = 600;
temperature_events = {}

class TemperatureEvent(object):
    """
    This class simply holds an RFID tag number and it's temperature points. It provides a method
    for returning the average temperature of all its points.
    """
    def __init__(self, tagNum):
        self.tagNum = tagNum
        self.temps = []
        
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

if __name__ == "__main__":
    # Create an API object using the key and tokens given to you
    api = BlueRoverWebApi.Api("HN8PZ+YHbe0JWjD+ZdI9TI/4WAVxq/RsTfW8Fv/aS9dyBEMk7ZCNUi4kzax2nSBg", "bpjYNcPNJUJknjn9NJY/ySREAU5VWcE3bxQYJOow")
    
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
                temp_event = TemperatureEvent(tagNum)
                temp_event.add_temperature(event['rfidTemperature'])
                temperature_events[tagNum] = temp_event
                
        # Since we want to write to file once every 3 hours, we collect data every 600 seconds 18 times
        if (count < 18):
            count += 1
        # Once we've collected 3 hours of data, we write to file
        else:
            # CSV header
            file_string = "Tag Num,Temperature Average\n"
            
            # Format the temperature data for CSV
            for event in temperature_events:
                file_string += str(event) + "," + str(temperature_events[event].get_average_temp()) + "\n"
            
            # Write the data to file
            f = open(str(time.time()) + ".csv", 'w')
            f.write(file_string)
            f.close()
            
            # Reset the temperature events for a new loop
            temperature_events = {}
            count = 1
        
        # Calculate the drift time for the loop so that the next one starts exactly at 600 seconds
        endTime = int(time.time())
        drift = endTime - startTime
        
        # Sleep
        time.sleep(POLLING_DURATION - drift)