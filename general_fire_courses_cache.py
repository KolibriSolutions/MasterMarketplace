import os
import django
import argparse
import sys

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='flush and refetch cache for courses')
    parser.add_argument('--mode', nargs='?', const=1, type=str, default='debug', help='debug/production')

    MODE = parser.parse_args().mode

    if MODE not in ["debug", "production"]:
        sys.exit(1)

    if MODE == 'debug':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings_development'
    elif MODE == 'production':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings'

    django.setup()

    from studyguide.models import CourseType
    from timeline.models import Year
    from registration.CourseBrowser import CourseBrowser
    from django.core.cache import cache

    cache.clear()

    for year in Year.objects.all():
        api = CourseBrowser(year=year.Begin.year)
        for type in CourseType.objects.all():
            codes = [c.Code for c in type.courses.filter(Year=year)]
            courses = [item for sublist in api.get_list_courses_data(codes) for item in sublist]