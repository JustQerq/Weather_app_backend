import datetime

def params2sql(received_params, params_dtypes: dict, params_aliases = None, relationship="=") -> list[str]:
    """Extract specified parameters from a dictionary and convert them into a list of SQL conditions

    Args:
        received_params (dict): dictionary of parameters to extract from
        params_dtypes (dict of str: func): parameters to extract with a conversion function for each parameter
        params_aliases (dict of str: str): parameter name alises to use in the SQL conditions
        relationship (str, optional): relationship between parameters and values. Defaults to "=".

    Returns:
        list(str): list
    """
    result = []
    
    if params_aliases is None:
        params_aliases = {}
        
    for param, dtype in params_dtypes.items():
        value = received_params.get(param, None)
        if value is not None:
            try:
                value = dtype(value)
                if type(value) == str:
                    value = f"'{value}'"
                else:
                    value = str(value)
            except:
                continue
            result.append(params_aliases.get(param, param) + relationship + value)
    
    return result


def validate_weather(entry):
    dt = entry.get("datetime", "")
    if (dt == ""):
        return False, []
    try:
        datetime.datetime.fromisoformat(dt)
    except:
        return False, []
    
    city = entry.get("city", None)
    if city == "":
        city = None
    
    country = entry.get("country", None)
    if country == "":
        country = None
    
    try:
        latitude = float(entry.get("latitude", None))
        longitude = float(entry.get("longitude", None))
        if ((latitude < -90) or (latitude > 90)) or((longitude < -180) or (longitude > 180)):
            latitude = None
            longitude = None
    except:
        latitude = None
        longitude = None
    
    if (city == None) and (country == None) and ((latitude == None) or (longitude==None)):
        return False, []
    
    try:
        temperature_c = float(entry.get("temperature_c", None))
        if temperature_c < -273.15:
            temperature_c = None
    except:
        temperature_c = None
    try:
        feelslike_c = float(entry.get("feelslike_c", None))
        if feelslike_c < -273.15:
            feelslike_c = None
    except:
        feelslike_c = None
    
    try:
        humidity = float(entry.get("humidity", None))
        if (humidity < 0) or (humidity > 100):
            humidity = None
    except:
        humidity = None
    
    try:
        wind_kph = float(entry.get("wind_kph", None))
        if wind_kph < 0:
            wind_kph = None
    except:
        wind_kph = None
    
    try:
        condition = str(entry.get("condition", None))
        if condition == "":
            condition = None
    except:
        condition = None
    
    if (temperature_c == None) and (feelslike_c == None) and (humidity == None) and (wind_kph==None) and (condition == None):
        return False, []
    
    return True, [dt, city, country, latitude, longitude, temperature_c, \
        feelslike_c, humidity, condition, wind_kph]