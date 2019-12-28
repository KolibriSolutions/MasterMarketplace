import os
import django
import argparse
import sys

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

    from registration.models import Registration, PlannedCourse
    import re
    from django.conf import settings
    from registration.CourseBrowser import CourseBrowser
    from registration.utils import pack_header

    coursereg = re.compile(settings.COURSECODEREGEX)
    api = CourseBrowser()

    for reg in Registration.objects.all():
        # iedereeen heeft al een courseplanning
        # try:
            # planning = reg.courseplanning
            # print(reg.Student+' already has planning')
            # continue
        # except:
        #     print('No reg for ')
        #     pass
        planning = reg.courseplanning
        # for OutOfFaculty, this is already completed.
        # l = list(set(coursereg.findall(reg.OutOfFacultyCourses)))
        l = reg.Electives.all()
        print('student {} (id:{})'.format(reg.Student, reg.Student.pk))
        for course in l:
            code = course.Code.upper()
            courseheader = api.get_course_data(code)
            if courseheader is None:
                print("skipped code {}".format(code))
                continue
            courseheader = pack_header(courseheader)
            if not PlannedCourse.objects.filter(Planning=planning, Code=courseheader['code']).exists():
                try:
                    q = int(courseheader['quartiles'][0])
                except ValueError:
                    q = 1
                c = PlannedCourse(Planning=planning, Year=1, Quartile=q, Code=courseheader['code'])
                c.save()
                print('planned {}'.format(c))
            else:
                print('was already planned, skipped {}'.format(courseheader['code']))

        print("{} Courses imported for {}".format(l.count(), reg.Student))
