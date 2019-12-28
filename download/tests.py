from general_test import ProjectViewsTestGeneral


class DownloadViewsTest(ProjectViewsTestGeneral):
    def setUp(self):
        self.app = 'download'
        super(DownloadViewsTest, self).setUp()

    def test_view_status(self):
        codes = [
            [['promotionfile', {'fileid': 0}], self.p_404],
            [['promotion_files', {'fileid': '9b73c48b-e05f-4e08-9db5-c8100119f673.pdf'}], self.p_404],

            # project attachments
            [['projectfile', {'ty':'a', 'fileid':0}], self.p_download_share],
            [['project_files', {'project_id': 0, 'fileid': '9b73c48b-e05f-4e08-9db5-c8100119f673.pdf'}], self.p_download_share],

            [['markdown_file', {'file_name': '9b73c48b-e05f-4e08-9db5-c8100119f673.pdf'}], self.p_404_anonymous],

            # student files
            [['studentfile', {'fileid': 0}], self.p_404],
            [['student_files', {'distid': self.dist.pk, 'fileid': '9b73c48b-e05f-4e08-9db5-c8100119f673.pdf'}], self.p_404],

            [['capacitygroupimage', {'fileid': 0}], self.p_404],
            [['capacitygroupimages', {'capid': 0, 'fileid': '9b73c48b-e05f-4e08-9db5-c8100119f673.pdf'}], self.p_404],

            [['masterprogramimage', {'fileid': 0}], self.p_404],
            [['masterprogramimages', {'capid': 0, 'fileid': '9b73c48b-e05f-4e08-9db5-c8100119f673.pdf'}], self.p_404],

        ]
        # Test for users, testing with nonexistent files for simplicity. So this always returns 404
        self.loop_code_user(codes)
        self.assertListEqual(self.allurls, [], msg="Not all URLs of this app are tested!")
