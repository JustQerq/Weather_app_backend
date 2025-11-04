import requests
import json


class RequestsManager:
    def __init__(self, base_url, request_urls=None):
        self.BASE_URL = base_url
        if request_urls is None:
            self.REQUEST_URLs = {}
        else:
            self.REQUEST_URLs = request_urls
    
    def get(self, request, **kwargs) -> dict:
        """Send HTTP GET request with the provided key-value parameter pairs

        Args:
            request (str): request name, must be stored in self.REQUEST_URLs
            **kwargs: key-value pairs of request query parameters, values must be strings

        Returns:
            dict: the received json file converted to a python dictionary
        """
        url = self.BASE_URL + self.REQUEST_URLs[request] + "?" + "&".join([f"{k}={v}" for k,v in kwargs.items()])
        response = requests.get(url).json()
        return response


class WeatherRequestsManager(RequestsManager):
    def __init__(self, api_key="3909896001fb4262833143125250211"):
        super().__init__(base_url="http://api.weatherapi.com/v1", request_urls={"current": "/current.json", "history": "/history.json", "autocomplete": "/search.json"})
        self.API_KEY = api_key
    
    def get(self, request, **kwargs) -> dict:
        url = self.BASE_URL + self.REQUEST_URLs[request] + f"?key={self.API_KEY}&" + "&".join([f"{k}={v}" for k,v in kwargs.items()])
        response = requests.get(url).json()
        return response


weather_req_manager = WeatherRequestsManager()

response = json.dumps(weather_req_manager.get("autocomplete", q="Lo Great Britain"), indent=4)
#response = weather_req_manager.get("current", q="New York")["location"]["country"]
print(response)