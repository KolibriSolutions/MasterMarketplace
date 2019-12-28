from general_test import ViewsTest


class GodPowersViewsTest(ViewsTest):
    def setUp(self):
        self.app = 'godpowers'
        super().setUp()

    def test_godpowers_views(self):
        # expected results
        # users order: harald, prof0, phd0, huug, god, student0
        codes = [
            [['clearcache', None], self.p_superuser],
            [['sessionlist', None], self.p_superuser],
            [['killsession', {'pk': 1}], self.p_superuser]
        ]

        # call the tests
        self.loop_code_user(codes)

        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
