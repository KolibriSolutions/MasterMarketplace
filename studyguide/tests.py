from general_test import ViewsTest
from timeline.utils import get_year
from .models import MasterProgram, CapacityGroup, MainCourse, CourseType


class StudyguideViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'studyguide'
        super().setUp()

    def test_studyguide_views(self):
        y = get_year()
        t = CourseType(Name='Test')
        t.save()

        c = MainCourse(Code="AAAAAA", Type=t, Year=y)
        c.save()

        # create dummy objects
        m = MasterProgram(Name='Electronic Systems', Info='')
        m.save()
        m.Group.add(CapacityGroup.objects.get(ShortName='ES'))
        m.MainCourses.add(c)
        m.save()

        codes = [
            [['yearslist', None], self.p_anonymous],

            [['courseslist', None], self.p_anonymous],
            [['courseslist', {'year': 1}], self.p_anonymous],  # autogenerated current year (id should be 1)
            [['courseslist', {'year': 2}], self.p_404_anonymous],  # nonexisting year

            [['masterprogramlist', None], self.p_anonymous],
            [['masterprogramlist', {'year': 0}], self.p_anonymous],  # all years
            [['masterprogramlist', {'year': 1}], self.p_anonymous],  # autogenerated current year (id should be 1)
            [['masterprogramlist', {'year': 2}], self.p_404_anonymous],  # nonexisting year
            [['addmasterprogram', None], self.p_support],
            [['editmasterprogram', {'pk': m.pk}], self.p_support],
            [['deletemasterprogram', {'pk': m.pk}], self.p_support],
            [['detailmasterprogram', {'pk': m.pk}], self.p_anonymous],
            [['editmasterprogramimages', {'pk': m.pk}], self.p_support],
            [['addmasterprogramimage', {'pk': m.pk}], self.p_support],

            # duplicate urls for masterprogram
            [['pathslist', None], self.p_anonymous],
            [['pathslist', {'year': 0}], self.p_anonymous],  # all years
            [['pathslist', {'year': 1}], self.p_anonymous],  # autogenerated current year (id should be 1)
            [['pathslist', {'year': 2}], self.p_404_anonymous],  # nonexisting year
            [['addpath', None], self.p_support],
            [['editpath', {'pk': m.pk}], self.p_support],
            [['deletepath', {'pk': m.pk}], self.p_support],
            [['detailpath', {'pk': m.pk}], self.p_anonymous],

            [['addcapacitygroup', None], self.p_support],
            [['editcapacitygroup', {'pk': m.pk}], self.p_support],
            [['deletecapacitygroup', {'pk': m.pk}], self.p_support],
            [['listcapacitygroups', None], self.p_anonymous],
            [['detailcapacitygroup', {'pk': m.id}], self.p_anonymous],
            [['detailcapacitygroup', {'shortname': 'ES'}], self.p_anonymous],
            [['editcapacitygroupimages', {'pk': m.pk}], self.p_support],
            [['addcapacitygroupimage', {'pk': m.pk}], self.p_support],

            [['maincourseadd', None], self.p_support],
            [['maincourseedit', {'code': 'AAAAAA', 'year': y.Begin.year}], self.p_support],
            [['maincoursedelete', {'code': 'AAAAAA', 'year': y.Begin.year}], self.p_support],
        ]

        # call the tests
        self.loop_code_user(codes)

        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
