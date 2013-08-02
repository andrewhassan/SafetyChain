from BlueRoverWebApi import BlueRoverWebApi
import sys

if __name__ == "__main__":
    api = BlueRoverWebApi.Api("HN8PZ+YHbe0JWjD+ZdI9TI/4WAVxq/RsTfW8Fv/aS9dyBEMk7ZCNUi4kzax2nSBg", "bpjYNcPNJUJknjn9NJY/ySREAU5VWcE3bxQYJOow")
    
    print api.call_api("/event", {"start_time": 0, "end_time": 1300000000, "page": 0}, False)
    