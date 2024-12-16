
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
def path_is_autonomous(path):
    """
    Define if path is autonomous or not 
    """
    nodes = path.split("=>")
    if len(nodes)==1:
            return True
    else:
            key = nodes[0].strip()
            autonomous = True
            for i in range(1,len(nodes)):
                if key!=nodes[i].strip():
                    autonomous = False
                    break
            return autonomous
