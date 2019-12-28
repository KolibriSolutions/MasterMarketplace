from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.urls import reverse

from general_test import ProjectViewsTestGeneral
from general_test import ViewsTest
from registration.models import Registration
from students.models import Application
from studyguide.models import CapacityGroup, MasterProgram
from .models import Project, ProjectLabel
from .utils import get_visible_projects, filter_visible_projects


class ProjectViewsTest(ProjectViewsTestGeneral):
    """
    All tests for projects views
    """

    def setUp(self):
        self.app = 'projects'
        super().setUp()
        self.projectlabel = ProjectLabel(Name='test', Color='bg-red')
        self.projectlabel.save()

    def test_view_status(self):
        """
        Test all views for their http statuscode from the proposals app for a list of usertypes.
        Tests for each page each:
        - timephase
        - proposal status
        - user (as defined in self.setup()

        :return:
        """
        s = self
        # setup environment

        code_general = [
            [['viewsharelink', {'token': 'blabla'}], [s.p_anonymous]],

            [['list', None], [s.p_all]],
            [['list', {'type_filter': 'graduation'}], [s.p_all]],
            [['list', {'type_filter': 'internship'}], [s.p_all]],
            [['list', {'type_filter': 'bleh'}], [s.p_forbidden]],
            [['favorites', None], [s.p_all]],
            [['favorites', {'type_filter': 'graduation'}], [s.p_all]],
            [['favorites', {'type_filter': 'internship'}], [s.p_all]],
            [['favorites', {'type_filter': 'bleh'}], [s.p_forbidden]],
            [['create', None], [s.p_staff_create]],
            [['chooseedit', None], [s.p_staff_proj_own]],
            [['chooseedit', {'status_filter':'active'}], [s.p_staff_proj_own]],
            [['listgroupprojects', None], [s.p_gr_admin]],
            [['listgroupprojects', {'status_filter':'active'}], [s.p_gr_admin]],
            [['pending', None], [s.p_pending]],
            [['labels', None], [s.p_staff]],
            [['createlabel', None], [s.p_staff]],
            [['editlabel', {'pk': self.projectlabel.pk}], [s.p_support]],
            [['activatelabel', {'pk': self.projectlabel.pk}], [s.p_support]],
            [['deletelabel', {'pk': self.projectlabel.pk}], [s.p_support]],
            [['stats', None], [s.p_staff]],
            [['stats', {'status_filter': 'active'}], [s.p_staff]],
            [['stats_personal', None], [s.p_staff]],
            [['contentpolicy', None], [s.p_support]],
            [['contentpolicycalc', None], [s.p_support]],
        ]
        # For projects with status:   1, 2, 3 (non public), 3 (public), 3 (in progress),  3 (finished)
        code_status = [
            [['addfile', {'ty': 'i', 'pk': self.p}],
             [s.p_all_this, s.p_responsible, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            [['editfile', {'ty': 'i', 'pk': self.p}],
             [s.p_all_this, s.p_responsible, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            [['edit', {'pk': self.p}],
             [s.p_all_this, s.p_responsible, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            [['copy', {'pk': self.p}],
             [s.p_all_this_create, s.p_all_this_create, s.p_all_this_create, s.p_staff_create, s.p_staff_create,
              s.p_staff_create]],
            [['distribute', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_responsible, s.p_responsible, s.p_responsible, s.p_forbidden]],
            [['progress', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_responsible, s.p_responsible, s.p_responsible, s.p_responsible]],
            [['details', {'pk': self.p}],
             [s.p_all_this_view, s.p_all_this_view, s.p_all_this_view, s.p_all, s.p_all, s.p_all]],
            [['upgradestatus', {'pk': self.p}],
             [s.p_all_this, s.p_responsible, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            # upgrade 1 to 2
            [['downgradestatusmessage', {'pk': self.p}],
             [s.p_forbidden, s.p_all_this, s.p_responsible, s.p_responsible, s.p_forbidden, s.p_forbidden]],
            # can't downgr.
            [['deleteproject', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            # only allowed via askdelete
            [['askdeleteproject', {'pk': self.p}],
             [s.p_responsible, s.p_responsible, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            [['sharelink', {'pk': self.p}],
             [s.p_all_this_study, s.p_all_this_study, s.p_all_this_study, s.p_staff_proj, s.p_staff_proj,
              s.p_staff_proj]],

        ]

        self.status = 1
        # info object with debug info if assertion fails
        info = {}
        # Test general page (not proposal specific)
        self.info['type'] = 'general'
        self.loop_code_user(code_general)

        # Testing proposal specific pages
        info['type'] = 'projects'
        self.loop_code_user(code_status)

        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")

    def test_progress_view(self):
        """
        Test visibilty for projects only for a given Specialization Path

        """
        self.project.Status = 3
        self.project.EndDate = datetime.now().date() + timedelta(days=2)
        self.project.save()
        self.status = 3
        # Test status 3p for students of specified Specialization Path
        view = 'projects:details'
        user = User.objects.get(username='r-s')
        program1 = MasterProgram(Name='program1')
        program1.save()
        program1.Group.add(CapacityGroup.objects.get(id=1))
        program1.save()
        program2 = MasterProgram(Name='program2')
        program2.save()
        program2.Group.add(CapacityGroup.objects.get(id=2))
        program2.save()
        self.client.force_login(user)
        self.info['user'] = user

        if self.debug:
            print("registered student to public proposal")
        r = Registration(Program=program1, Student=user, Origin='bsc_ele_tue', Cohort=2012, State=1)
        r.save()
        response = self.client.get(reverse(view, kwargs={'pk': self.project.id}))
        self.assertEqual(response.status_code, 200)

        if self.debug:
            print("registered student to proposal of his group")
        self.project.Program.add(program1)
        self.project.save()
        response = self.client.get(reverse(view, kwargs={'pk': self.project.id}))
        self.assertEqual(response.status_code, 200)

        if self.debug:
            print("registered student to proposal of other group")
        self.project.Program.remove(program1)
        self.project.Program.add(program2)
        self.project.save()
        response = self.client.get(reverse(view, kwargs={'pk': self.project.id}))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_apply_buttons(self):
        """
        Test if the apply/retract buttons show at the right time

        :return:
        """
        self.project.Status = 3
        self.project.EndDate = datetime.now().date() + timedelta(days=2)
        self.status = 3
        self.project.Apply = 'system'
        self.project.save()
        if self.debug:
            print("Testing apply buttons for student")
        user = User.objects.get(username='r-s')
        self.client.force_login(user)
        view = "projects:details"

        if self.debug:
            print("Test apply")
        txt = "Apply</a>"
        response = self.client.get(reverse(view, kwargs={"pk": self.project.id}))
        self.assertContains(response, txt)

        if self.debug:
            print("Test retract")
        a = Application(Student=user, Project=self.project)
        a.save()
        txt = "Retract Application</a>"
        response = self.client.get(reverse(view, kwargs={"pk": self.project.id}))
        self.assertContains(response, txt)

        if self.debug:
            print("Test apply")
        self.project.Apply = 'supervisor'
        self.project.save()
        txt = "Apply to this project by contacting the supervisor."
        response = self.client.get(reverse(view, kwargs={"pk": self.project.id}))
        self.assertContains(response, txt)
        self.client.logout()

    def test_links_visible(self):
        """
        Test if the visible buttons do return a 200

        :return:
        """
        self.project.Status = 3
        self.project.EndDate = datetime.now().date() + timedelta(days=2)
        self.status = 3
        self.project.Apply = 'system'
        self.project.save()
        if self.debug:
            print("Testing all links for users")

        views = ["projects:details"]
        for view in views:
            self.info['view'] = view
            ViewsTest.links_in_view_test(self, reverse(view, kwargs={"pk": self.project.id}))

    def test_visible_projects(self):
        self.project.Status = 3
        self.project.save()

        proj = self.project
        proj.pk = 11
        proj.StartDate = None
        proj.EndDate = None
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 12
        proj.StartDate = None
        proj.EndDate = datetime.now().date() - timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 13
        proj.StartDate = None
        proj.EndDate = datetime.now().date() + timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 14
        proj.StartDate = None
        proj.EndDate = datetime.now().date()
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 15
        proj.StartDate = datetime.now().date()
        proj.EndDate = datetime.now().date()
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 16
        proj.StartDate = datetime.now().date()
        proj.EndDate = None
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 17
        proj.StartDate = datetime.now().date() - timedelta(days=1)
        proj.EndDate = None
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 18
        proj.StartDate = datetime.now().date() + timedelta(days=1)
        proj.EndDate = None
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 19
        proj.StartDate = datetime.now().date() - timedelta(days=1)
        proj.EndDate = datetime.now().date() + timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 20
        proj.StartDate = datetime.now().date() - timedelta(days=1)
        proj.EndDate = datetime.now().date() - timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 21
        proj.StartDate = datetime.now().date() + timedelta(days=1)
        proj.EndDate = datetime.now().date() + timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        proj = self.project
        proj.pk = 22
        proj.StartDate = datetime.now().date() + timedelta(days=1)
        proj.EndDate = datetime.now().date() - timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='ES')
        proj.save()

        # to test that non-ele students cannot see this projects.
        proj = self.project
        proj.pk = 23
        proj.StartDate = datetime.now().date() - timedelta(days=1)
        proj.EndDate = datetime.now().date() + timedelta(days=1)
        proj.Group = CapacityGroup.objects.get(ShortName='EPE')
        proj.save()

        visible_all = [11, 13, 14, 15, 16, 17, 19, 23]
        visible_oth = [11, 13, 14, 15, 16, 17, 19]

        # # test student ELE
        user = User.objects.get(username='e-s')
        # using get_visible_projects
        v = get_visible_projects(user)
        v = [x.pk for x in v]
        self.assertListEqual(visible_all, v, msg="Error, Visible projects ELE student, on get_visible_projects.")
        # using filter_visible_projects
        v = filter_visible_projects(Project.objects.filter(Status=3), user)
        v = [x.pk for x in v]
        self.assertListEqual(visible_all, v, msg="Error, filter projects ELE student, on filter_visible_projects.")

        # # test student non-ELE, from ES. Cannot view the project from EPE
        user = User.objects.get(username='r-s')
        # using get_visible_projects
        v = get_visible_projects(user)
        v = [x.pk for x in v]
        self.assertListEqual(visible_oth, v, msg="Error, visible projects other student, on get_visible_projects.")
        # using filter_visible_projects
        v = filter_visible_projects(Project.objects.filter(Status=3), user)
        v = [x.pk for x in v]
        self.assertListEqual(visible_oth, v, msg="Error, filter projects other student, on filter_visible_projects.")
