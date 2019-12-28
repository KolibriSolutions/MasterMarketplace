from django.test import TestCase, Client, override_settings
from django.urls.resolvers import URLResolver
from django.utils.module_loading import import_module
from django.conf import settings
from registration.utils import create_api_key
from django.contrib.auth.models import User
from index.models import UserMeta
from django.urls import reverse
from registration.models import Registration, Planning
from studyguide.models import MasterProgram
import json

# disable cache for all tests
@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
                   EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend', EMAIL_FILE_PATH='./test_mail.log')
@override_settings(
    MIDDLEWARE_CLASSES=[mc for mc in settings.MIDDLEWARE
                        if mc != 'tracking.middleware.TelemetryMiddleware']
)
@override_settings(
    CHANNEL_LAYERS={},
    TESTING=True
)
class RegistrationApiViewsTest(TestCase):
    def setUp(self):
        self.app = 'registration.api'
        self.client = Client()
        # to test that each page is at least tested once, check if all urls of the app are tested.
        urlpatterns = import_module(self.app + '.urls', 'urlpatterns').urlpatterns
        self.allurls = [x.name for x in urlpatterns if type(x) != URLResolver]

        self.u = User(username='student0')
        self.u.email = 'student0' + '@' + settings.STAFF_EMAIL_DOMAINS[0]
        self.u.save()
        m = UserMeta(User=self.u)
        m.save()
        mp = MasterProgram(Name='Test')
        mp.save()
        r = Registration(Student=self.u, Cohort=2100, Program=mp)
        r.save()
        p = Planning(Registration=r)
        p.save()


    def _test_request(self, link, data, expected):
        try:
            response = self.client.post(link, data=data)
            response_code = response.status_code
        except:
            response_code = 500

        self.assertEqual(response_code, expected, msg='Expected status code {} but got {} for {}'.format(expected, response_code, link))


    def test_registration_api_valid(self):
        #test links with valid code
        data = {
            'username' : 'student0',
            'apikey' : create_api_key(self.u)
        }

        self._test_request(reverse('registration:registration_api:api_add_year'), data, 200)
        self._test_request(reverse('registration:registration_api:api_remove_year'), data, 200)
        self._test_request(reverse('registration:registration_api:api_get_planning'), data, 200)
        planning = {
            'Y1Q1' : [],
            'Y1Q2': [],
            'Y1Q3': [],
            'Y1Q4': [],
            'Y2Q1': [],
            'Y2Q2': [],
            'Y2Q3': [],
            'Y2Q4': []
        }
        data['planning'] = json.dumps(planning)
        self._test_request(reverse('registration:registration_api:api_save_planning'), data, 200)

    def test_registration_api_invalid(self):
        #test links with invalid or missing code
        data = {
            'username' : 'student0',
            'apikey' : 'BANAAN'
        }

        self._test_request(reverse('registration:registration_api:api_add_year'), data, 403)
        self._test_request(reverse('registration:registration_api:api_remove_year'), data, 403)
        self._test_request(reverse('registration:registration_api:api_get_planning'), data, 403)
        planning = {
            'Y1Q1' : [],
            'Y1Q2': [],
            'Y1Q3': [],
            'Y1Q4': [],
            'Y2Q1': [],
            'Y2Q2': [],
            'Y2Q3': [],
            'Y2Q4': []
        }
        data['planning'] = json.dumps(planning)
        self._test_request(reverse('registration:registration_api:api_save_planning'), data, 403)