
"""""
This file defines additional functions required for various purposes.
"""
from datetime import datetime

def difference_date(date1,date2):
    """""
    Calculate the diffrence between two dates given by days 
    """
    date_format = "%Y%m%d%H%M"
    date1 = datetime.strptime(date1, date_format)
    date2 = datetime.strptime(date2, date_format)
    return (date2 - date1).total_seconds() / 86400

def transform_date(date):
    """""
    Transform a timestamp to a date  
    """
    parsed_date = datetime.strptime(date, "%Y%m%d%H%M")
    formatted_date = parsed_date.strftime("%Y-%m-%d")
    return formatted_date 
