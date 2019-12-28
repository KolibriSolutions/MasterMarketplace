import os
import django
import argparse
import sys


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="dump or load course codes for the studyguide")
    parser.add_argument('--djangomode', nargs='?', const=1, type=str, default='debug', help='debug/production')
    parser.add_argument('--mode', nargs='?', const=1, type=str, default='dump', help='dump/load')
    DJANGOMODE = parser.parse_args().djangomode
    MODE = parser.parse_args().mode

    if DJANGOMODE not in ["debug", "production"]:
        print("Please use --djangomode debug or --djangomode production")
        sys.exit(1)

    if DJANGOMODE == 'debug':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings_development'
    elif DJANGOMODE == 'production':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings'

    django.setup()

    from studyguide.models import Course, MainCourse, CourseType
    from timeline.models import Year
    import yaml
    from registration.CourseBrowser import CourseBrowser

    if MODE == "dump":
        courses = [{
            "code" : c.Code,
            "year" : c.Year.pk
        } for c in Course.objects.all()]
        with open('studyguide.yaml', 'w') as stream:
            yaml.dump(courses, stream, default_flow_style=False)
        sys.exit(0)

    if MODE == "load":
        ctype = CourseType.objects.get(Name="Free Elective")
        with open('studyguide.yaml', 'r') as stream:
            courses = yaml.load(stream)

        for c in courses:
            try:
                year = Year.objects.get(pk=c['year'])
            except Year.DoesNotExist:
                continue
            api = CourseBrowser(year=year.Begin.year)
            header = api.get_course_data(c['code'])
            if header is None:
                print("Could not import {} in {}".format(c['code'], year.Begin.year))
            else:
                c_obj = MainCourse(Code=c['code'], Type=ctype, Year=year)
                c_obj.save()
                print("Saved {}".format(c_obj))

        sys.exit(0)