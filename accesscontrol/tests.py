from general_test import ViewsTest
from .models import AllowedAccess, Origin


class AccessControlViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'accesscontrol'
        super().setUp()

    def test_accesscontrol_views(self):
        # create dummy objects
        o = Origin.objects.get(Name='ES')
        o.save()
        a = AllowedAccess(Email='user@test.nl', Origin=o)
        a.save()

        codes = [
            [['grant', None], self.p_support],
            [['list', None], self.p_support],
            [['import', None], self.p_support],
            [['edit', {'pk': a.pk}], self.p_support],
            [['revoke', {'pk': a.pk}], self.p_support],
            [['createorigin', None], self.p_support],
            [['editorigin', {'pk': o.pk}], self.p_support],
            [['listorigins', None], self.p_support],

        ]

        # call the tests
        self.loop_code_user(codes)
        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
