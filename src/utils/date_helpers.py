from datetime import datetime, timedelta
import calendar

def get_week_range(year, month, week_num):
    first_day = datetime(year, month, 1)
    days_to_monday = (7 - first_day.weekday()) % 7
    if days_to_monday == 0:
        days_to_monday = 7
    start_date = first_day + timedelta(days=days_to_monday * (week_num - 1))
    end_date = start_date + timedelta(days=6)
    last_day = calendar.monthrange(year, month)[1]
    end_date = min(end_date, datetime(year, month, last_day))
    return start_date, end_date
