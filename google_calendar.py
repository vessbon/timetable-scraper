from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from scraper import Lesson
from datetime import datetime, timedelta
from colors import closest_color_id


# If modifying SCOPES, delete token.json
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If not (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def get_or_create_calendar(service, calendar_name: str):
    # Check all calendars
    calendars = service.calendarList().list().execute()

    for cal in calendars.get("items", []):
        if cal["summary"] == calendar_name:
            return cal["id"]

    # If not found, create a new one
    new_calendar = {
        "summary": calendar_name,
        "timeZone": "Europe/Stockholm"
    }

    created_calendar = service.calendars().insert(body=new_calendar).execute()
    return created_calendar["id"]

def add_lesson_to_calendar(service, lesson: Lesson, calendar_id: int = "primary"):
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

    colors = service.colors().get().execute()["event"]
    lesson_hex = lesson.color

    color_id = 8 # default: graphite -> gray
    if lesson_hex is not None:
        color_id = closest_color_id(lesson_hex, colors)

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
        },
        "colorId": color_id
    }

    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Added: {created_event.get('summary')} at {created_event['start']['dateTime']}")

def add_lessons_to_calendar(service, lessons: list[Lesson], calendar_id: int = "primary"):
    for lesson in lessons:
        add_lesson_to_calendar(service, lesson, calendar_id)

def clear_unique_days(service, calendar_id: str, lessons: list[Lesson]):
    # Get all unique dates from the lessons
    unique_dates = {lesson.date for lesson in lessons}

    for d in unique_dates:
        clear_day(service, calendar_id, d)

def clear_day(service, calendar_id: str, target_date: datetime):
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = start_time + timedelta(days=1)

    event_results = service.events().list(
        calendarId=calendar_id,
        timeMin=start_time.isoformat() + "Z",
        timeMax=end_time.isoformat() + "Z",
        singleEvents=True
    ).execute()

    events = event_results.get("items", [])
    for event in events:
        service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()

    print(f"Cleared {len(events)} events on {target_date}.")

def clear_week(service, calendar_id: str, week: int, year: int):
    # Monday of that ISO week
    start_date = datetime.fromisocalendar(year, week, 1) # monday of specified week
    for i in range(7):
        clear_day(service, calendar_id, start_date + timedelta(days=i))

