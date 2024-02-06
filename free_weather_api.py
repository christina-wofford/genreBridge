
def freeWeatherAPI():
    requests = __import__('requests')
    api_key ='3a81f96482874955949212505233006'
    url = 'http://api.weatherapi.com/v1/current.json?key=' + api_key + '&q=21046&aqi=yes'
    freeWeatherAPI = requests.get(url).json()
    print(freeWeatherAPI)