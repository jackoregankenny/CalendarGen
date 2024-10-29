from datetime import date
from dateutil.easter import easter
from dateutil.relativedelta import relativedelta, MO, TH, FR

def get_irish_holidays(year):
    holidays = {}
    
    # Fixed dates
    holidays[date(year, 1, 1)] = "New Year's Day"
    holidays[date(year, 3, 17)] = "St. Patrick's Day"
    holidays[date(year, 12, 25)] = "Christmas Day"
    holidays[date(year, 12, 26)] = "St. Stephen's Day"
    
    # First Mondays
    holidays[date(year, 2, 1) + relativedelta(weekday=MO(+1))] = "St. Brigid's Day"
    holidays[date(year, 5, 1) + relativedelta(weekday=MO(+1))] = "May Bank Holiday"
    holidays[date(year, 6, 1) + relativedelta(weekday=MO(+1))] = "June Bank Holiday"
    holidays[date(year, 8, 1) + relativedelta(weekday=MO(+1))] = "August Bank Holiday"
    holidays[date(year, 10, 1) + relativedelta(weekday=MO(+1))] = "October Bank Holiday"
    
    # Easter-related
    easter_date = easter(year)
    holidays[easter_date] = "Easter Sunday"
    holidays[easter_date + relativedelta(days=1)] = "Easter Monday"
    holidays[easter_date - relativedelta(days=2)] = "Good Friday"
    
    return holidays

def get_uk_holidays(year):
    holidays = {}
    
    # Fixed dates
    holidays[date(year, 1, 1)] = "New Year's Day"
    holidays[date(year, 12, 25)] = "Christmas Day"
    holidays[date(year, 12, 26)] = "Boxing Day"
    
    # Last Monday in May
    holidays[date(year, 5, 31) + relativedelta(weekday=MO(-1))] = "Spring Bank Holiday"
    
    # Last Monday in August
    holidays[date(year, 8, 31) + relativedelta(weekday=MO(-1))] = "Summer Bank Holiday"
    
    # Easter-related
    easter_date = easter(year)
    holidays[easter_date - relativedelta(days=2)] = "Good Friday"
    holidays[easter_date + relativedelta(days=1)] = "Easter Monday"
    
    return holidays

def get_us_holidays(year):
    holidays = {}
    
    # Fixed dates
    holidays[date(year, 1, 1)] = "New Year's Day"
    holidays[date(year, 7, 4)] = "Independence Day"
    holidays[date(year, 11, 11)] = "Veterans Day"
    holidays[date(year, 12, 25)] = "Christmas Day"
    
    # Third Monday in January
    holidays[date(year, 1, 1) + relativedelta(weekday=MO(+3))] = "Martin Luther King Jr. Day"
    
    # Third Monday in February
    holidays[date(year, 2, 1) + relativedelta(weekday=MO(+3))] = "Presidents' Day"
    
    # Last Monday in May
    holidays[date(year, 5, 31) + relativedelta(weekday=MO(-1))] = "Memorial Day"
    
    # First Monday in September
    holidays[date(year, 9, 1) + relativedelta(weekday=MO(+1))] = "Labor Day"
    
    # Second Monday in October
    holidays[date(year, 10, 1) + relativedelta(weekday=MO(+2))] = "Columbus Day"
    
    # Fourth Thursday in November (Thanksgiving)
    holidays[date(year, 11, 1) + relativedelta(weekday=TH(+4))] = "Thanksgiving"
    
    return holidays

def get_holidays(year, country):
    holiday_functions = {
        'irish': get_irish_holidays,
        'uk': get_uk_holidays,
        'us': get_us_holidays,
    }
    
    if country in holiday_functions:
        return holiday_functions[country](year)
    return {}