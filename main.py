from datetime import datetime, date
import json
import requests

class Lesson:
    def __init__(self, lesson_data):
        self.name = lesson_data["texts"][0]
        self.teachers = [t.strip() for t in lesson_data["texts"][1].split(",")]
        self.room = lesson_data["texts"][2]

        self.day_of_week = lesson_data["dayOfWeekNumber"]

        self.time_start = datetime.strptime(
            lesson_data["timeStart"], "%H:%M:%S").strftime("%H:%M")
        self.time_end = datetime.strptime(
            lesson_data["timeEnd"], "%H:%M:%S").strftime("%H:%M")

        self.gui_id = lesson_data["guidId"]

        dt = lesson_data["date"]
        self.year = dt.year
        self.month = dt.month
        self.week = dt.isocalendar()[1]
        self.day = dt.day

    def __str__(self):
        teachers_str = ", ".join(self.teachers)
        return f"{self.name} ({self.time_start}-{self.time_end}) in {self.room} with {teachers_str}"

    def __repr__(self):
        return f"<Lesson: {self.name} ({self.time_start}-{self.time_end})>"

class Timetable:
    def __init__(self, username: str, headers: dict, cookies: dict, start_week: int = 0, end_week: int = -1):
        self.username = username
        self.headers = headers
        self.cookies = cookies

        self.start_week = start_week
        self.end_week = end_week
        if self.end_week == -1:
            self.end_week = self.start_week
        if self.start_week > self.end_week:
            raise ValueError(f"Start week ({self.start_week}) cannot be greater than end week ({self.end_week}).")
        self.weeks = list(range(self.start_week, self.end_week + 1))

        self.selection = self._get_signature()
        self.render_key = self._get_key()

        self.data = {}
        if len(self.weeks) == 1:
            self.data = [self._get_timetable(week=self.start_week)]
        else:
            self.data = self._get_timetables(weeks=self.weeks)

        self.lessons = []
        self._update_lessons()

    def __str__(self) -> str:
        return json.dumps(self.data, indent=4, default=str)

    def get_lessons_week(self, week: int) -> list:
        """
        Retrieves all the lesson data from the specified timetable week number.
        :arg week: The week of the lesson. Accepts a value from 1-52.
        :return: A list of lesson objects.
        """
        lessons = []
        for tt in self.data:
            if tt["week"] == week:
                for lesson in self.lessons:
                    lessons.append(lesson)
        return lessons

    def get_lessons_day(self, day: int | str) -> list:
        """
        Retrieves all the lesson data from the specified timetable days. Sorts the lessons by their starting time.
        :arg day: The day of the lesson. Accepts either a value from 1-5, or a string containing the name of the day of the week.
        :return: A list of lesson objects, sorted by lesson start time.
        """
        lessons = []
        for lesson in self.lessons:
            if lesson.day_of_week == day:
                lessons.append(lesson)
        return sorted(lessons, key=lambda x: datetime.strptime(x.time_start, "%H:%M"))

    def _update_lessons(self):
        """
        Saves all the identified lessons from current timetable data to the instance.
        """
        for tt in self.data:
            for lesson in tt["lessonInfo"]:
                lesson = Lesson(lesson_data=lesson)
                self.lessons.append(lesson)

    def _get_timetable(self, week: int) -> dict:
        url = "https://web.skola24.se/api/render/timetable"
        year = datetime.now().year

        payload = {
            'renderKey': self.render_key,
            'host': 'halmstad.skola24.se',
            'unitGuid': 'OWM1YWRhYTEtYTNmYi1mNzYzLWI5NDItZjkzZjE3M2VhNjA4',
            'schoolYear': '56aca0af-cc20-445e-bc4a-b96bbc0d7e23',
            'startDate': None,
            'endDate': None,
            'scheduleDay': 0,
            'blackAndWhite': False,
            'width': 1280,
            'height': 720,
            'selectionType': 4,
            'selection': self.selection,
            'showHeader': False,
            'periodText': '',
            'week': week,
            'year': year,
            'privateFreeTextMode': False,
            'privateSelectionMode': None,
            'customerKey': '',
            'personalTimetable': False,
        }

        response = requests.post(url, headers=self.headers, cookies=self.cookies, json=payload)
        data = response.json()["data"]
        data["week"] = week
        data["year"] = year

        heading_days = {}
        for element in data["textList"]:
            if element["type"] == "HeadingDay":
                heading_days[element["parentId"]] = element["text"]

        for lesson in data["lessonInfo"]:
            date_str = heading_days[lesson["dayOfWeekNumber"]]
            date_part = date_str.split()[1]
            dt = datetime.strptime(f"{date_part}/{year}", "%d/%m/%Y")
            lesson["date"] = dt.date()

        return data

    def _get_timetables(self, weeks: list) -> list:
        timetables = []
        for week in weeks:
            timetables.append(self._get_timetable(week=week))
        return timetables

    def _get_signature(self) -> str:
        url = "https://web.skola24.se/api/encrypt/signature"
        payload = {
            'signature': self.username,
        }

        response = requests.post(url, headers=self.headers, cookies=self.cookies, json=payload)
        return response.json()["data"]["signature"]

    def _get_key(self) -> str:
        url = "https://web.skola24.se/api/get/timetable/render/key"
        response = requests.post(url, headers=self.headers, cookies=self.cookies)
        return response.json()["data"]["key"]


class User:
    def __init__(self, username, headers, cookies, start_week: int = 0, end_week: int = -1):
        self.username = username
        self.timetable = Timetable(username, headers, cookies, start_week, end_week)


default_cookies = {
    'ASP.NET_SessionId': 'c4wbrv3whgvioo2eiillzhpo',
    'legacyuicookiestd': '!X3miW1kLqEJETGPqOzcOU+M1NwuqTppGW3BX+PrIumZBAMDeGbLGD+2SARRvOmmXwZs0V5Jp0cw83iI=',
    's24_tenant': 'mXGxBdJZAud7HhUuy6j/q//W2XRaFBcCSEACWvgXSAo=',
    'TS01fb1e5e': '01b91fe1da1143ca1b35d50a817d6756198dfb54400533509b3cb2e9a70879a0e2ac8405b3b7c678fb1431da5e49efc2e6ed80e6a3bb52de9d204ef9524cdbb68d2dd02762',
}

default_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.6',
        'Connection': 'keep-alive',
        'Origin': 'https://web.skola24.se',
        'Referer': 'https://web.skola24.se/timetable/timetable-viewer/halmstad.skola24.se/Kattegattgymnasiet/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Scope': '8a22163c-8662-4535-9050-bc5e1923df48',
}

today = date.today()
week_num = today.isocalendar()[1]

user = User("antnor", default_headers, default_cookies, 39)
timetable = user.timetable

print(timetable)
print(timetable.lessons)

for l in timetable.get_lessons_day(2):
    print(l)
