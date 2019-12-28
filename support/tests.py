from django.contrib.auth.models import User

from general_test import ViewsTest
from .models import Promotion, MailTemplate
from support.consumers import MailProgressConsumer

class SupportViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'support'
        super().setUp()

        # create dummy user for upgrade/downgrade
        self.dummy = User(username='dummy')
        self.dummy.save()

        t = MailTemplate(
            Message='test',
            Subject='test',
            RecipientsStaff='[]',
            RecipientsStudents='[]',
        )
        t.pk = 1
        t.save()

    def test_support_views(self):
        codes = [
            [['mailinglist', None], self.p_support],
            [['mailinglisttemplate', {'pk': 1}], self.p_support],
            [['mailingconfirm', None], self.p_forbidden],  # requires post
            [['mailingtemplates', None], self.p_support],
            [['deletemailingtemplate', {'pk': 1}], self.p_support],

            [['addpromotion', None], self.p_support],
            [['editpromotions', None], self.p_support],
            [['listusers', None], self.p_support],
            [['toggledisable', {'pk': self.dummy.id}], [302 if x == 200 else x for x in self.p_support]],
            [['userinfo', {'pk': 1}], self.p_support],
            [['usergroups', {'pk': 1}], self.p_support],
            [['liststaff', None], self.p_support],
            [['liststaffprojects', {'pk': 1}], self.p_support],
            [['liststudents', None], self.p_staff],
            # [['clearcacheuserlist', None], self.p_support],
            [['groupadministratorsform', None], self.p_support],
            [['editmenulinks', None], self.p_support],
        ]

        p = Promotion(Organization='Kolibri', Text='Kolibri Solutions is awesome!')
        p.save()

        # call the tests
        self.loop_code_user(codes)

        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")

