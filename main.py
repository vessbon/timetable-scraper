from google_calendar import get_calendar_service, add_lessons_to_calendar, get_or_create_calendar
from scraper import Timetable

service = get_calendar_service()


class Student:
    def __init__(self, username: str, school: str, start_week: int = 0, end_week: int = -1):
        self.username = username
        self.timetable = Timetable(username, school, start_week, end_week)

student = Student("your_username", "your_school",  39, 42)
timetable = student.timetable

result = timetable.lessons
#result = timetable.get_lessons_week(39)
#result = timetable.get_lessons_day(4)

calendar_id = get_or_create_calendar(service, "School") # leave calendar name empty for primary calendar
add_lessons_to_calendar(service=service, lessons=result, calendar_id=calendar_id)
