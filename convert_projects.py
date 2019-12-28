import argparse
import os
import sys

import django

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="import es projects")
    parser.add_argument('--mode', nargs='?', const=1, type=str, default='debug', help='debug/production')
    MODE = parser.parse_args().mode

    if MODE not in ["debug", "production"]:
        print("Please use --mode debug or --mode production")
        sys.exit(1)

    if MODE == 'debug':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings_development'
    elif MODE == 'production':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings'

    django.setup()

    from registration.CourseBrowser import CourseBrowser
    from registration.utils import pack_header
    from projects.models import Project
    from studyguide.models import MainCourse
    from timeline.utils import get_year
    api = CourseBrowser()

    for proj in Project.objects.all():
        l = proj.RequiredCourses.all()
        print('proj {} (id:{})'.format(proj, proj.pk))
        for course in l:
            code = course.Code.upper()
            courseheader = api.get_course_data(code)
            if courseheader is None:
                print("skipped code {}".format(code))
                continue
            courseheader = pack_header(courseheader)
            if not proj.RecommendedCourses.filter(Code=code).exists():
                c = MainCourse.objects.get(Code=code, Year=get_year())
                proj.RecommendedCourses.add(c)
                proj.save()
                print('Added {}'.format(c))
            else:
                print('was already planned, skipped {}'.format(courseheader['code']))

        print("{} Courses imported for {}".format(l.count(), proj))
