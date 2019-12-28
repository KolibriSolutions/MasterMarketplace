import os
import django
import argparse
import sys
import json

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='exports registraions in json')
    parser.add_argument('--mode', nargs='?', const=1, type=str, default='debug', help='debug/production')
    parser.add_argument('--cohort', nargs='?', const=1, type=int, default=-1, help='cohort to export')
    parser.add_argument('--no-projects', action='store_true')

    MODE, COHORT, NOPROJECTS = parser.parse_args().mode, parser.parse_args().cohort, parser.parse_args().no_projects

    if MODE not in ["debug", "production"]:
        sys.exit(1)

    if MODE == 'debug':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings_development'
    elif MODE == 'production':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings'

    django.setup()

    from registration.models import Registration
    from projects.models import Project

    data = {
        'registrations' : {},
        'projects' : {}
    }

    if COHORT != -1:
        regs = Registration.objects.filter(Cohort=COHORT)
    else:
        regs = Registration.objects.all()
    for reg in regs:
        data['registrations'][reg.Student.email] = reg.Program.Name.split('-')[0]

    if NOPROJECTS:
        print(json.dumps(data))
        sys.exit(0)

    groupcount = {}
    for p in Project.objects.filter(Status=3):
        try:
            groupcount[p.Group.ShortName] += 1
        except KeyError:
            groupcount[p.Group.ShortName] = 1

    data['projects'] = groupcount

    print(json.dumps(data))