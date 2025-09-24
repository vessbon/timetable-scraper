from google_calendar import *
from scraper import Timetable

service = get_calendar_service()


class Student:
    def __init__(self, username: str, school: str, start_week: int = 0, end_week: int = -1):
        self.username = username
        self.school = school
        self.start_week = start_week
        self.end_week = end_week

        self.timetable = Timetable(username, school, start_week, end_week)

student = Student("antnor", "Kattegattgymnasiet",  39, 42)
timetable = student.timetable

result = timetable.lessons
#result = timetable.get_lessons_week(39)
#result = timetable.get_lessons_day(4)

calendar_id = get_or_create_calendar(service, "School") # leave calendar name empty for primary calendar

# Remove overlapping lessons from calendar
clear_unique_days(service, calendar_id, result)

# Add selected lessons to calendar
add_lessons_to_calendar(service=service, lessons=result, calendar_id=calendar_id)
