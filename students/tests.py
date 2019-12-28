from datetime import datetime, timedelta

from django.urls import reverse

from general_test import ProjectViewsTestGeneral
from students.models import Application, StudentFile


class StudentsViewsTest(ProjectViewsTestGeneral):
    def setUp(self):
        self.app = 'students'
        super(StudentsViewsTest, self).setUp()
        # self.debug=True
        self.f = StudentFile(
            Caption='testfiletype',
            Distribution=self.dist,
        )
        self.f.save()

    def test_view_status(self):
        """
        Test pages related to applications

        :return:
        """
        # Track for the project, with trackhead t-h
        s = self
        # General pages
        code_general = [
            [['list_applications', None], [s.p_student_only]],
            [['addfile', {'dist': self.dist.pk}], [s.p_student_dist]],
            [['editfile', {'dist': self.dist.pk, 'file': self.f.pk}], [s.p_student_dist]],
            [['files', {'dist': self.dist.pk}], [s.p_all_this_dist]],
        ]
        # Status:                               1           2           3 notpublic 3public 3+exec  3+finished
        # For projects that can be applied to via marketplace
        code_project_apply = [
            [['apply', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_student_only, s.p_student_only, s.p_forbidden]],
            [['confirmapply', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_student_only, s.p_student_only, s.p_forbidden]],
        ]
        # For projects that cannot be applied using marketplace
        code_project_notapply = [
            [['apply', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
            [['confirmapply', {'pk': self.p}],
             [s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden, s.p_forbidden]],
        ]
        code_application_none = [
            [['retractapplication', {'application_id': 0}], [s.p_student404]],
            # [['prioUp', {'application_id': 0}],             [student404]],
            # [['prioDown', {'application_id': 0}],           [student404]]
        ]

        self.status = 1
        # info object with debug info if assertion fails
        info = {}
        # Test general page (not project specific)
        if self.debug:
            print("Testing general")
        info['type'] = 'general'
        if self.debug:
            print('General 1')
        self.loop_code_user(code_general)

        # Project specific
        if self.debug:
            print("Testing project apply")
        info['type'] = 'apply system'
        self.project.Apply = 'system'
        self.project.save()
        self.loop_code_user(code_project_apply)

        # Project specific, not apply
        if self.debug:
            print("Testing project apply for contacting supervisor")
        info['type'] = 'apply supervisor'
        self.project.Apply = 'supervisor'
        self.project.save()
        self.loop_code_user(code_project_notapply)

        # application pages
        if self.debug:
            print("Testing project apply for applications student only")
        info['type'] = 'apply general'
        self.project.Status = 3
        self.project.EndDate = datetime.now().date() + timedelta(days=2)
        self.project.Progress = None
        self.project.save()
        a = Application(Student=self.users.get('r-s'), Project=self.project)
        a.save()
        self.loop_code_user(code_application_none)

        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")

    def test_apply_retract(self):
        """
        Test apply retract pages in status 3

        :return:
        """
        self.project.Status = 3
        self.project.EndDate = datetime.now().date() + timedelta(days=2)
        self.project.Progress = None
        self.project.Apply = 'system'
        self.project.save()

        # student
        s = self.users.get('r-s')

        # Test apply
        view = "students:apply"
        self.client.force_login(s)
        response = self.client.get(reverse(view, kwargs={"pk": self.p}))
        self.assertEqual(response.status_code, 200, msg="Student cannot apply to project!")
        self.assertTrue(Application.objects.exists(), msg="Application is not made!")

        # Test retract
        view = "students:retractapplication"
        app = Application.objects.get(Student=s)
        response = self.client.get(reverse(view, kwargs={"application_id": app.id}))
        self.assertEqual(response.status_code, 200, msg="Student cannot retract application!")
        self.assertFalse(Application.objects.exists(), msg="Application is not retracted!")

        self.client.logout()
