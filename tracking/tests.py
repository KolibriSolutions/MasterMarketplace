from django.contrib.auth.models import User

from general_test import ViewsTest
from .models import UserLogin, RegistrationTracking


class TrackingViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'tracking'
        super().setUp()

    def testViews(self):
        codes = [
            [['listuserlog', None], self.p_superuser],
            [['statuslist', None], self.p_superuser],
            [['applicationlist', None], self.p_superuser],
            [['distributionslist', None], self.p_superuser],
            [['registrationchanges', None], self.p_support],
            [['userdetail', {'pk': 1}], self.p_superuser],
        ]

        # create dummy objects
        u = UserLogin(Subject=User.objects.get(username='r-s'))
        u.save()

        u = RegistrationTracking(Student=User.objects.get(username='r-s'))
        u.save()

        # call the tests
        self.loop_code_user(codes)

        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
