import os
import django
import argparse
import sys

# Initialy populate an empty django database with the required groups, and possibly dummy data for testing.

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Populate the database with initial values")
    parser.add_argument('--mode', nargs='?', const=1, type=str, default='debug', help='debug/production')
    parser.add_argument('--create-dummy-data', dest='createDummyData', action='store_true', help='if activated dummy data is generated')
    parser.set_defaults(createDummyData=False)
    DUMMY, MODE = parser.parse_args().createDummyData, parser.parse_args().mode

    if MODE not in ["debug", "production"]:
        print("Please use --mode debug or --mode production")
        sys.exit(1)

    if MODE == 'debug':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings_development'
    elif MODE == 'production':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'MasterMarketplace.settings'

    django.setup()

    from django.contrib.auth.models import Group
    from studyguide.models import CapacityGroup, CourseType
    from accesscontrol.models import Origin
    from students.models import FileExtension

    # setup all groups
    g, created = Group.objects.get_or_create(name='studyadvisors')
    if created:
        print("creating studyadvisors")

    g, created = Group.objects.get_or_create(name='directors')
    if created:
        print("creating directors")

    g, created = Group.objects.get_or_create(name='supervisors')
    if created:
        print("creating supervisors")

    g, created = Group.objects.get_or_create(name='assistants')
    if created:
        print("creating assistants")

    g, created = Group.objects.get_or_create(name='unverified')
    if created:
        print("creating unverified")

    g, created = Group.objects.get_or_create(name='groupadministrator')
    if created:
        print("creating groupadministrator")

    # setup capacitygroups
    Groups = (
        ("EES", "Electrical Energy Systems"),
        ("ECO", "Electro-optical Communication"),
        ("EPE", "Electromechanics and Power Electronics"),
        ("ES", "Electronic Systems"),
        ("IC", "Integrated Circuits"),
        ("CS", "Control Systems"),
        ("SPS", "Signal Processing System"),
        ("PHI", "Photonic Integration"),
        ("EM", "Electromagnetics"),
        ("--", "None"),
    )

    for group in Groups:
        c, created = CapacityGroup.objects.get_or_create(ShortName=group[0], FullName=group[1])
        if created:
            print("creating {}-{}".format(group[0], group[1]))

    # get a default origin for accesscontrol
    o, created = Origin.objects.get_or_create(Name='ELE')
    if created:
        print("creating origin ELE")

    # file extensions
    f = FileExtension(Name='pdf')
    f.save()
    f = FileExtension(Name='xls')
    f.save()
    f = FileExtension(Name='xlsx')
    f.save()
    f = FileExtension(Name='zip')
    f.save()

    # course types
    CourseType.objects.all().delete()
    c = CourseType(Name='Core Course')
    c.save()
    c = CourseType(Name='Free Elective')
    c.save()
    c = CourseType(Name='Professional Development')
    c.save()


    if not DUMMY:
        #End of non dummy generation
        sys.exit(0)

    from django.contrib.auth.models import Group, User
    from index.models import UserMeta
    from projects.models import Project
    import random

    #generate test users, proposals and applictions for debug purpose
    print("populating tables with debug objects")

    NUMPROFS = 20
    NUMPHDS = 30
    NUMSTDS = 30
    NUMPROPOSALS = 50

    type1staff = Group.objects.get(name="supervisors")
    type2staff = Group.objects.get(name="assistants")
    director = Group.objects.get(name="directors")
    studyadvisors = Group.objects.get(name="studyadvisors")

    profs = list(type1staff.user_set.all())
    phds = list(type2staff.user_set.all())

    print("creating {} professors".format(NUMPROFS))
    for i in range(0, NUMPROFS):
        try:
            prof = User.objects.create_user('professor{}'.format(i), 'professor{}@tue.nl'.format(i), 'marketplace')
            prof.first_name = "professor"
            prof.last_name = str(i)
            prof.groups.add(type1staff)
            prof.save()
            profs.append(prof)
        except:
            print(str(i)+" not created")
        prof = User.objects.get(username='professor{}'.format(i))
        try:
            mta = UserMeta()
            mta.Fullname = "Professor-" + str(i)
            mta.Studentnumber = 0
            mta.User = prof
            mta.save()
            print("usermeta prof" + str(i))
        except:
            print(str(i) + " prof usermeta not created")

    print("creating {} phders".format(NUMPHDS))
    for i in range(0, NUMPHDS):
        try:
            phd = User.objects.create_user('phd{}'.format(i), 'phd{}@tue.nl'.format(i), 'marketplace')
            phd.first_name = "phd"
            phd.last_name = str(i)
            phd.groups.add(type2staff)
            phd.save()
            phds.append(phd)
        except:
            print(str(i)+" not created")
        phd = User.objects.get(username='phd{}'.format(i))
        try:
            mta = UserMeta()
            mta.Fullname = "phd-" + str(i)
            mta.Studentnumber = 0
            mta.User = phd
            mta.save()
            print("usermeta phd" + str(i))
        except:
            print(str(i) + " phd usermeta not created")

    stds = []
    print("creating {} students".format(NUMSTDS))
    for i in range(0, NUMSTDS):
        try:
            std = User.objects.create_user('std{}'.format(i), 'std{}@tue.nl'.format(i), 'marketplace')
            std.first_name = "std"
            std.last_name = str(i)
            std.save()
            stds.append(std)
        except:
            print(str(i)+" not created")
        std = User.objects.get(username='std{}'.format(i))
        try:
            mta = UserMeta()
            mta.Fullname = "student-" + str(i)
            mta.Studentnumber = str(i) + str(i) + str(i) + str(i) + str(i)
            mta.User = std
            mta.save()
            print("usermeta" + str(i))
        except:
            print(str(i)+" usermeta not created")

    print("creating the studyadvisor user")
    try:
        supp = User.objects.create_user('johndoe', 'j.doe@tue.nl', 'marketplace')
        supp.first_name = "John"
        supp.last_name = "Doe"
        supp.groups.add(studyadvisors)
        supp.save()
    except:
        print("no studyadvisor created")
    supp = User.objects.get(username='johndoe')
    try:
        mta = UserMeta()
        mta.Fullname = 'John Doe'
        mta.User = supp
        mta.save()
    except:
        print('Studyadvisor usermeta not created')

    print("creating the director user")
    try:
        supp = User.objects.create_user('janedoe', 'j.doe.1@tue.nl', 'marketplace')
        supp.first_name = "Jane"
        supp.last_name = "Doe"
        supp.groups.add(director)
        supp.save()
    except:
        print("no director created")
    supp = User.objects.get(username='janedoe')
    try:
        mta = UserMeta()
        mta.Fullname = 'Jane Doe'
        mta.User = supp
        mta.save()
    except:
        print('director usermeta not created')

    def flip(x):
        """

        :param x:
        :return:
        """
        return True if random.random() < x else False

    print("creating proposals")
    for i in range(0, NUMPROPOSALS):
        try:
            p = Project()
            p.Title = "project{}".format(i)
            p.ResponsibleStaff = random.choice(profs)
            p.Group = CapacityGroup.objects.get(ShortName=random.choice(Groups)[0])
            p.NumstudentsMin = random.randint(1,2)
            p.NumstudentsMax = random.randint(p.NumstudentsMin, 5)
            p.GeneralDescription = "stuff about project. autogenerated with number {}".format(i)
            p.StudentsTaskDescription = "students have to do stuff woop woop"
            p.ECTS = 15
            #p.Private = None
            # p.Image = random.choice(["niels.png", "crying.png"])
            # p.Status = random.choice(Proposal.StatusOptions)[0]
            p.Status = 3
            p.save() #save already to activate the manytomany field of assistants
            numphd = random.choice([1,2])
            ass1 = random.choice(phds)
            p.Assistants.add(ass1)
            if numphd == 2:
                phds.remove(ass1)
                ass2 = random.choice(phds)
                p.Assistants.add(ass2)
                phds.append(ass1)
            p.save()
            print('{} created'.format(p))
        except:
            print(str(i)+"th proposal not created")
