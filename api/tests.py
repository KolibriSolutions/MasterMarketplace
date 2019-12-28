from django.contrib.auth.models import User

from index.models import UserMeta

from general_test import ProjectViewsTestGeneral
from studyguide.models import CapacityGroup


class ApiViewsTest(ProjectViewsTestGeneral):
    def setUp(self):
        self.app = 'api'
        super().setUp()

        self.dummy = User(username='dummy')
        self.dummy.save()
        m = UserMeta(User=self.dummy)
        m.save()

    def test_view_status(self):
        s = self
        g = CapacityGroup(ShortName='ES', FullName='ES')
        g.save()
        codes_general = [
            # [['getgroupadmins', None], s.p_forbidden],  # god only
            # [['getgroupadminsarg', {'group': GroupOptions[0][0]}], s.p_forbidden],
            [['listpublished', None], s.p_all],
            [['listpublishedpergroup', None], s.p_all],
            [['listpublishedtitles', None], s.p_all],
            [['api', None], s.p_all],
            [['getpublisheddetail', {'pk': self.p}], s.p_forbidden],  # as proposal is not visible yet.
            [['getgroupadmins', {'type': 'read', 'pk': g.pk}], s.p_support],
            [['getgroupadmins', {'type': 'write', 'pk': g.pk}], s.p_support],
            [['verifyassistant', {'pk': self.dummy.id}], self.p_support],
            # use a dummy user without type2staffunverified

        ]
        # EndDate = datetime.now().date() - timedelta(days=2),
        self.loop_code_user(codes_general)
        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
