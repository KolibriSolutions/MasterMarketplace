"""
General functions/classes used in tests.
"""
import re
import sys
import traceback
from datetime import datetime, timedelta

from django.contrib.auth.models import User, Group
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.utils.module_loading import import_module

from accesscontrol.models import Origin, AllowedAccess
from index.models import UserAcceptedTerms
from index.models import UserMeta
from projects.models import Project
from studyguide.models import CapacityGroup, GroupAdministratorThrough
from students.models import Distribution
from django.urls.resolvers import URLResolver


# disable cache for all tests
@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
                   EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                   EMAIL_FILE_PATH='./test_mail.log',
                   MIDDLEWARE_CLASSES=[mc for mc in settings.MIDDLEWARE
                                       if mc != 'tracking.middleware.TelemetryMiddleware'],
                   # CHANNEL_LAYERS={},
                   TESTING=True
                   )
class ViewsTest(TestCase):
    """
    Class with testclient to test views. Some functions to setup data in the database.
    """

    def setUp(self):
        """
        Setup test data, like users and groups.
        """
        # super(ViewsTest, self).setUp()
        # whether to produce output, please override this on app level if debug is required.
        self.debug = False

        # to test that each page is at least tested once, check if all urls of the app are tested.
        urlpatterns = import_module(self.app + '.urls', 'urlpatterns').urlpatterns
        self.allurls = [x.name for x in urlpatterns if type(x) != URLResolver]

        # the client used for testing
        self.client = Client()
        # info string to show debug info in case of test assertion failure
        self.info = {}

        # Create capacity groups
        groups = (
            ("EES", "Electrical Energy Systems"),
            ("ECO", "Electro-Optical Communications"),
            ("EPE", "Electromechanics and Power Electronics"),
            ("ES", "Electronic Systems"),
            ("IC", "Integrated Circuits"),
            ("CS", "Control Systems"),
            ("SPS", "Signal Processing Systems"),
            ("PHI", "Photonic Integration"),
            ("EM", "Electromagnetics")
        )
        for group in groups:
            g, created = CapacityGroup.objects.get_or_create(ShortName=group[0], FullName=group[1])
            setattr(self, 'cg_'+group[0], g)
            assert created, "Group {} not created!".format(group[0])

        # Create groups and users
        self.create_groups()
        self.create_users()

        gra = User.objects.get(username='gr-g')
        grw = User.objects.get(username='grw-g')

        g = GroupAdministratorThrough(User=gra, Super=False,
                                      Group=CapacityGroup.objects.all()[0])
        g.save()
        g2 = GroupAdministratorThrough(User=grw, Super=True,
                                       Group=CapacityGroup.objects.all()[0])
        g2.save()
        # users order:               r-y, r-d, r-s, t-s, e-s, r-r, t-r, r-a, t-a, gr-g,grw-g,god,ano
        self.p_forbidden =          [403, 403, 403, 403, 403, 403, 403, 403, 403, 403, 403, 403, 302]
        self.p_superuser =          [403, 403, 403, 403, 403, 403, 403, 403, 403, 403, 403, 200, 302]
        self.p_all =                [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 302]
        self.p_anonymous =          [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200]
        self.p_redirect =           [302, 302, 302, 302, 302, 302, 302, 302, 302, 302, 302, 302, 302]  # everyone

        self.p_support =            [200, 200, 403, 403, 403, 403, 403, 403, 403, 403, 403, 200, 302]
        self.p_directors =          [403, 200, 403, 403, 403, 403, 403, 403, 403, 403, 403, 200, 302]
        self.p_student_only =       [403, 403, 200, 200, 200, 403, 403, 403, 403, 403, 403, 403, 302]
        self.p_student_dist =       [403, 403, 403, 200, 403, 403, 403, 403, 403, 403, 403, 403, 302]
        self.p_student_ele =        [403, 403, 403, 403, 200, 403, 403, 403, 403, 403, 403, 403, 302]
        self.p_student404 =         [403, 403, 404, 404, 404, 403, 403, 403, 403, 403, 403, 403, 302]
        self.p_staff =              [200, 200, 403, 403, 403, 200, 200, 200, 200, 200, 200, 200, 302]
        self.p_staff_proj =         [200, 403, 403, 403, 403, 200, 200, 200, 200, 200, 200, 200, 302]
        self.p_staff_proj_own=      [200, 403, 403, 403, 403, 200, 200, 200, 200, 403, 403, 200, 302]
        self.p_staff_create =       [403, 403, 403, 403, 403, 200, 200, 200, 200, 403, 200, 200, 302]
        self.p_gr_admin =           [403, 403, 403, 403, 403, 403, 403, 403, 403, 200, 200, 200, 302]

        self.p_all_this =           [200, 403, 403, 403, 403, 403, 200, 403, 200, 403, 200, 200, 302]
        self.p_all_this_create =    [403, 403, 403, 403, 403, 403, 200, 403, 200, 403, 200, 200, 302]
        self.p_all_this_study =     [200, 403, 403, 403, 403, 403, 200, 403, 200, 200, 200, 200, 302]
        self.p_all_this_dist =      [200, 403, 403, 200, 403, 403, 200, 403, 200, 403, 403, 200, 302]  # for viewing student files, without groupadmin.
        self.p_all_this_view =      [200, 403, 403, 200, 403, 403, 200, 403, 200, 200, 200, 200, 302]  # for viewing distributed project
        self.p_responsible =        [200, 403, 403, 403, 403, 403, 200, 403, 403, 403, 200, 200, 302]
        self.p_responsible_nonadmin=[403, 403, 403, 403, 403, 403, 200, 403, 403, 403, 403, 200, 302]
        self.p_pending =            [403, 403, 403, 403, 403, 200, 200, 200, 200, 200, 200, 200, 302]
        self.p_god_admin =          [200, 403, 403, 403, 403, 403, 403, 403, 403, 403, 200, 200, 302]
        # used to test filesdownload (with sharelinrelinrelink proposals)
        self.p_download_share =     [404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 403]
        self.p_404 =                [404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 302]
        self.p_404_anonymous =      [404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404, 404]

    def create_groups(self):
        """
        Create all groups for the system.

        :param self:
        :return:
        """
        # setup all groups
        self.group_names = [
            'studyadvisors',
            'supervisors',
            'assistants',
            'directors',
            'unverified',
            'groupadministrator'
        ]
        for g in self.group_names:
            group, created = Group.objects.get_or_create(name=g)
            assert created
            # make group object accessable as a class variable. < self.type1staff > etc.
            setattr(self, g, group)

    def create_users(self):
        """
        Takes self.usernames and creates users based on this. The last character of the username determnines the group
        WARNING: This only generates users and assign groups.
        It does not assign roles (like groupadministration and trackhead models).
        """
        # create testusers using the naming-patern: [r t]-[s p 1 2 u 3 t ]
        # r=random (any person of the given type), t=this(for this project), gr=readonly groupadmin, grw=rw-groupadmin.
        # r=responsible, a=assistant, y=studYadvisor, s=Student, d=director, g=groupadmin
        self.usernames = [
            'r-y',  # studyadvisor
            'r-d',  # director
            'r-s',  # student
            't-s',  # student with distribution
            'e-s',  # student of ELE
            'r-r',  # responsible
            't-r',  # responsible of this project
            'r-a',  # assistant
            't-a',  # assistant of this project
            'gr-g',  # group administrator read only
            'grw-g',  # group administrator read/write
            'sup',  # god user (superuser)
            'ano',  # anonymous user
        ]
        # , 'r-e', 't-e']  # possible external staff.
        origin = Origin(Name='ELE')
        origin.save()
        origin2 = Origin(Name='ES')
        origin2.save()
        origin2.Groups.add(CapacityGroup.objects.get(ShortName='ES'))
        origin2.save()
        # Create the users and assign groups/roles.
        self.users = {}
        for n in self.usernames:
            if n != 'ano':
                u = User(username=n)
                u.email = n + '@' + settings.STAFF_EMAIL_DOMAINS[0]
                u.save()
                m = UserMeta(User=u)
                m.save()
                x = n.split('-')[-1]
                if x == 'y':
                    u.groups.add(self.studyadvisors)
                elif x == 'r':
                    u.groups.add(self.supervisors)
                elif x == 'a':
                    u.groups.add(self.assistants)
                elif x == 'd':
                    u.groups.add(self.directors)
                elif x == 'g':
                    u.groups.add(self.groupadministrator)
                elif n == 'sup':
                    u.groups.add(self.studyadvisors)
                    u.groups.add(self.supervisors)  # hack to make testing easier.
                    u.is_superuser = True
                    u.is_staff = True
                elif x == 's':  # student
                    u.email = n + '@' + settings.STUDENT_EMAIL_DOMAINS[0]
                    if n == 'e-s':
                        a = AllowedAccess(  # ELE student
                            Email=u.email,
                            Origin=origin
                        )
                        a.save()
                        u.usermeta.Department = 'ELE'  # usermeta.Department is derived from accesscontrol on saml login.
                        u.usermeta.save()
                    else:
                        a = AllowedAccess(  # non-ELE student
                            Email=u.email,
                            Origin=origin2
                        )
                        a.save()
                        u.usermeta.Department = 'ES'
                        u.usermeta.save()
                # save user
                u.save()
                self.users[n] = u
                ua = UserAcceptedTerms(User=u)
                ua.save()

    def links_in_view_test(self, sourceurl, skip=[]):
        """
        Find all links in a response and check if they return status 200.

        :param sourceurl: the page which is parsed to test the links on the page.
        :param skip: some urls to not check.
        :return:
        """
        for username in User.objects.all().values_list('username', flat=True):
            if username == 'ano':
                continue
            user = User.objects.get(username=username)
            self.client.force_login(user)
            response = self.client.get(sourceurl)
            urls = re.findall('/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+/',
                              str(response.content))
            urls = [x for x in urls if (">" not in x
                                        and "<" not in x
                                        and "//" not in x
                                        and "/static/" not in x
                                        and "/logout/" not in x
                                        and "tracking/live/" not in x
                                        and "tracking/viewnumber/" not in x
                                        and "js_error_hook" not in x
                                        and x not in skip)]

            for link in urls:  # select the url in href for all a tags(links)
                if link in skip:
                    continue
                if self.debug:
                    print('url: {}'.format(link))
                self.info['user'] = user.username
                self.view_test_status(link, 200)
            self.client.logout()

    def loop_code_user(self, codes):
        """
        Test all views for all users

        :param codes: list of views and expected status codes
        :return:
        """
        for page, status in codes:
            if self.debug:
                self.info['reverse'] = str(page)
                self.info['statuscodes'] = status
            view = self.app + ":" + page[0]
            if any(isinstance(i, list) for i in status):
                # we're dealing with proposals status tests here
                ProjectViewsTestGeneral.loop_user_status(self, view, status, page[1])
            else:
                # normal test without proposals
                self.loop_user(view, status, page[1])
            # remove the page from the list of urls of this app.
            if page[0] in self.allurls: self.allurls.remove(page[0])

    def loop_user(self, view, status, kw=None):
        """
        Loop over the provided pages with status code for each user and test these.

        :param view: name of the page, for reverse view
        :param status: array of http status that is expected for each user
        :param kw: keyword args for the given view.
        :return:
        """
        for i, username in enumerate(self.usernames):
            self.info['user'] = username
            self.info['kw'] = kw
            if self.debug:
                self.info['user-index'] = i
            # log the user in
            if username != 'ano':
                u = User.objects.get(username=username)
                if self.debug:
                    self.info['user-groups'] = u.groups.all()
                    self.info['user-issuper'] = u.is_superuser
                self.client.force_login(u)
            self.view_test_status(reverse(view, kwargs=kw), status[i])
            if username != 'ano':
                self.client.logout()

    def view_test_status(self, link, expected):
        """
        Test a given view

        :param self: the instance for the testcase class, containing self.client, the testclient instance.
        :param link: a link to a view to test
        :param expected: the expected response code
        :return:
        """
        try:
            response = self.client.get(link)
            response_code = response.status_code
            if response_code == 403 or expected == 403:
                try:
                    exception = list(response.context[0])[0]["exception"]
                except:
                    try:
                        exception = list(response.context[0])[0]["Message"]
                    except:
                        # exception = response.context  # this is a large amount of information
                        exception = 'Reason not found in context!'
                self.info['exception'] = exception
            else:
                if response_code == 404:
                    for d in response.context.dicts:
                        try:
                            self.info['exception'] = d['Message']
                            break
                        except:
                            continue
                else:
                    self.info['exception'] = "no 403"
        except Exception as e:
            response_code = 500
            print("Error: {}".format(e))
            self.info['exception'] = '500 {}'.format(e)
            traceback.print_exc(file=sys.stdout)

        self.assertEqual(response_code, expected,
                         msg='Expected status code {} but got {} for {} info: {}.'
                         .format(expected, response_code, link, self.info))


class ProjectViewsTestGeneral(ViewsTest):
    """
    Functions to test pages related to proposals/projects
    """

    def setUp(self):
        """
        Initialization test data for proposals/projects

        :param self: self
        :return:
        """
        # create users and groups in parent function
        super(ProjectViewsTestGeneral, self).setUp()

        # The project used for testing, created as project in the past to set publicvisible() false
        self.project = Project(Title="testproject",
                               ResponsibleStaff=User.objects.get(username='t-r'),
                               Group=CapacityGroup.objects.all()[0],
                               NumStudentsMin=1,
                               NumStudentsMax=1,
                               GeneralDescription="Test general description",
                               StudentsTaskDescription="Test student task description",
                               Status=1,
                               EndDate=datetime.now().date() - timedelta(days=2),
                               StartDate=datetime.now().date() - timedelta(days=7),
                               )

        self.project.save()
        self.p = self.project.id
        self.project.Assistants.add(User.objects.get(username='t-a'))
        # self.project.ExternalStaff.add(self.users.get('t-e'))
        self.project.save()
        self.dist = Distribution(Student=self.users.get('t-s'), Project=self.project)
        self.dist.save()

    def loop_user_status(self, view, status, kw=None):
        """
        Test all users and proposal status for a given page. Called from self.all_pages_test()

        :param view: name of the page, for reverse view
        :param status: array of http status that is expected for each user
        :param kw: keyword args for the given view.
        :return:
        """
        assert isinstance(status, list)
        for i, username in enumerate(self.usernames):
            self.info['user'] = username
            self.info['kw'] = kw
            if self.debug:
                self.info['user-index'] = i
            if username != 'ano':
                # log the user in
                u = User.objects.get(username=username)
                if self.debug:
                    self.info['user-groups'] = u.groups.all()
                    self.info['user-issuper'] = u.is_superuser
                self.client.force_login(u)
            # check for each given status from the status-array
            l = len(status)
            for status0 in range(0, l):
                if self.debug:
                    print("Testing status {}".format(status0 + 1))
                self.status = status0 + 1
                if status0 >= 3:
                    # For mastermarket, status 4 is equal to (status 3 with publicvisible true)
                    self.status = 3
                    self.project.EndDate = datetime.now().date() + timedelta(days=2)
                    self.project.Progress = None
                    if status0 == 4:  # Progress is set to "in progress"
                        self.project.Progress = 1
                    elif status0 == 5:  # Progress is set to 'finished'
                        self.project.Progress = 2
                else:
                    self.project.Progress = None
                    self.project.EndDate = datetime.now().date() - timedelta(days=2)
                self.project.save()
                self.info['status'] = self.status
                self.info['progress'] = self.project.Progress
                # Expected response code
                expected = status[status0][i]
                # Reset the project status, because it changes after a test call to upgrade/downgrade
                self.project.Status = self.status
                self.project.save()
                self.view_test_status(reverse(view, kwargs=kw), expected)
            # user logout
            if username != 'ano':
                self.client.logout()
