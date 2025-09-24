from google_calendar import get_calendar_service
from datetime import datetime
from scraper import Timetable, Lesson

service = get_calendar_service()


class Student:
    def __init__(self, username: str, school: str, start_week: int = 0, end_week: int = -1):
        self.username = username
        self.timetable = Timetable(username, school,  start_week, end_week)


def add_lesson_to_calendar(lesson: Lesson):
    # Split time strings like "08:30"
    start_hour, start_minute = map(int, lesson.time_start.split(":"))
    end_hour, end_minute = map(int, lesson.time_end.split(":"))

    # Combine lesson.date (a datetime.date) with times
    start_time = datetime.combine(lesson.date, datetime.min.time()).replace(
        hour=start_hour, minute=start_minute
    )
    end_time = datetime.combine(lesson.date, datetime.min.time()).replace(
        hour=end_hour, minute=end_minute
    )

    event = {
        "summary": lesson.name,
        "location": lesson.school,
        "description": f"In {lesson.room} with {', '.join(lesson.teachers)}.",
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Europe/Stockholm"
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Europe/Stockholm"
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 10},
            ]
        }
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"Added: {created_event.get('summary')} at {created_event['start']['dateTime']}")

student = Student("you_username_here", "your_school_here",  39)
timetable = student.timetable

l = timetable.get_lessons_day(4)[0]
add_lesson_to_calendar(l)
