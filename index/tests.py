from django.shortcuts import reverse
from django.utils import timezone

from general_test import ViewsTest
from .models import FeedbackReport


class IndexViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'index'
        super().setUp()

        self.fb = FeedbackReport(
            Reporter=self.users['sup'],
            Url='/',
            Feedback='Test Feedback',
            Timestamp=timezone.now(),
            Status=1,
        )
        self.fb.save()

    def test_index_views(self):
        self.info = {}
        codes = [
            [['index', None], self.p_anonymous],
            [['about', None], self.p_anonymous],
            [['profile', None], self.p_all],
            [['feedback_form', None], self.p_all],
            [['feedback_submit', None], self.p_all],
            [['list_feedback', None], self.p_superuser],
            [['confirm_feedback', {'pk': self.fb.id}], self.p_superuser],
            [['close_feedback', {'pk': self.fb.id}], self.p_superuser],
            [['changesettings', None], self.p_all],
            [['termsaccept', None], self.p_redirect],
            [['markdown_upload', None], self.p_forbidden],  # forbidden because referer is missing in request.
            [['robots', None], self.p_anonymous],
        ]
        self.loop_code_user(codes)
        # check if all urls are processed, except login and logout
        self.assertListEqual(self.allurls, ['login', 'logout'], msg="Not all URLs of this app are tested!")

    def test_links_visible(self):
        """
        Test if all links shown in a view go to a page with status 200.
        Used to test if all visible menu items are actually available for the given user in the given view.

        :return:
        """
        self.info = {}
        views = ["index:index", 'index:profile']
        for phase in range(1, 8):
            for view in views:
                self.info['view'] = view
                ViewsTest.links_in_view_test(self, reverse(view))
