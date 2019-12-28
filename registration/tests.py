from django.contrib.auth.models import User

from general_test import ViewsTest
from studyguide.models import MainCourse, MasterProgram, CourseType
from timeline.models import Year
from .models import Registration
from django.utils.timezone import timedelta, now


# from .api.tests import *


class RegistrationViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'registration'
        super().setUp()
        # create dummy objects
        yr = Year(Name='testyear', Begin=(now() - timedelta(days=40)).date(), End=(now() + timedelta(days=40)).date())
        yr.save()
        ct = CourseType(Name="Core Course")
        ct.save()
        ct = CourseType(Name='Professional Development')
        ct.save()

        c1 = MainCourse(Code='5SHA0', Type=ct, Year=yr)
        c1.save()
        c2 = MainCourse(Code='5SHB0', Type=ct, Year=yr)
        c2.save()

        m = MasterProgram(Name='Electronic Systems')
        m.save()
        m.Group.add(self.cg_ES)
        m.MainCourses.add(c1)
        m.MainCourses.add(c2)
        m.save()

        r = Registration()
        r.Student = User.objects.get(username='e-s')
        r.Cohort = 2017
        r.Origin = 'bsc_ele_tue'
        r.Program = m
        r.Approved = True
        r.State = 1
        r.save()

    def test_registration(self):
        codes = [
            [['registrationform', None], self.p_student_ele],
            [['listall', None], self.p_support],
            [['listall', {'cohort': 2012}], self.p_support],
            [['approve', {'pk': 1}], self.p_support],
            [['disapprove', {'pk': 1}], self.p_support],
            [['stats', None], self.p_staff],
            [['stats', {'cohort': 2017}], self.p_staff],
            [['courseplanner', None], self.p_student_ele],
            [['courseplanner', {'student_pk': User.objects.get(username='e-s').pk}], self.p_support],
            [['addotherdep', None], self.p_student_ele],
            [['addotheruni', None], self.p_student_ele],
            [['requestapproval', None], self.p_student_ele],
            [['approvalform', None], self.p_student_ele],
            [['approvalformsupport', {'pk': User.objects.get(username='e-s').id}], self.p_support],

            [['deadlineform', {'t': 1}], self.p_support],
            [['deadlinedescription', None], self.p_support],
            [['deadlines', None], self.p_all],
        ]
        # call the tests
        self.loop_code_user(codes)
        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
