import json
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache


class CourseBrowser:
    BASEURL = "https://coursebrowser.nl/osiris/api/tue/{year}/"
    COURSEHEADER = BASEURL + "course/{code}/header/"
    LISTCOURSES = BASEURL + "faculty/courses/EE/GS/"

    def __init__(self, year=None):
        if year is None:
            now = datetime.now()
            if now.month <= 6:
                self.year = now.year - 1
            else:
                self.year = now.year
        else:
            self.year = year
        try:
            with open('proxies.json', 'r') as stream:
                self.proxies = json.loads(stream.readlines()[0].strip('\n'))
        except:
            self.proxies = {}

        self.session = requests.session()
        self.session.headers['User-Agent'] = 'MasterMarketplace by Kolibri Solutions'
        self.session.headers['From'] = 'mastermarketplace@tue.nl'
        if self.proxies != {}:
            self.session.proxies.update(self.proxies)

    def get_all_course_codes(self):
        if settings.TESTING:
            return []
        data = cache.get('coursecodes_{}'.format(self.year))
        if data is None:
            r = self.session.get(self.LISTCOURSES.format(year=self.year))
            if r.status_code != 200:
                return None
            cache.set('coursecodes_{}'.format(self.year), r.json(), 2 * 7 * 24 * 60 * 60)  # two weeks
            return r.json()
        else:
            return data

    def get_all_course_data(self):
        if settings.TESTING:
            return []
        data = cache.get('coursesdata_{}'.format(self.year))
        if data is None:
            codes = self.get_all_course_codes()
            data = self.get_list_courses_data(codes)
            cache.set('coursesdata_{}'.format(self.year), data, 2 * 7 * 24 * 60 * 60)  # two weeks
        return data

    def get_list_courses_data(self, courses):
        if settings.TESTING:
            return []
        data = []
        for course in courses:
            header = self.get_course_data(course)
            if header is not None:
                data.append(header)
        return data

    def get_course_data(self, course):
        header = cache.get("{}_{}".format(course, self.year))
        if header is None:
            r = self.session.get(self.COURSEHEADER.format(code=course, year=self.year))
            if r.status_code != 200:
                # maybe this code was from prev year?? Try last year...
                r = self.session.get(self.COURSEHEADER.format(code=course, year=self.year-1))
                if r.status_code != 200:
                    return None
            header = r.json()
            # bsc courses are also allowed!
            # for c in header:
                # if c['type'] != "GS":
                #     return None
            cache.set("{}_{}".format(course, self.year), header, 2 * 7 * 24 * 60 * 60)  # two weeks
        return header
