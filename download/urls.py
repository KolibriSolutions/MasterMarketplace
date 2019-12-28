from django.urls import path, re_path
from django.conf import settings
from . import views

# define all kinds of file downloads here.
# Files can be downloaded using their filename (for backward compatibility with file edit) or using their object ID
app_name = 'download'

reguuid = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}.[A-z]{1,5}"  # regex for uuid with extension

urlpatterns = [
    # public files
    # url(r'publicfile/(?P<fileid>[0-9]+)$', views.PublicFiles, name='publicfile'),

    # markdown images
    re_path(settings.MARKDOWN_IMAGE_UPLOAD_FOLDER+'/(?P<file_name>' + reguuid + ')$', views.markdown_file_download, name='markdown_file'),

    # proposal attachments
    path('projectfile/<str:ty>/<int:fileid>', views.project_files, name='projectfile'),
    re_path(r'project_(?P<project_id>[0-9]+)/(?P<fileid>' + reguuid + ')$', views.project_files, name='project_files'),
    # direct url

    # promotion logos
    path('promotionfile/<int:fileid>', views.promotion_files, name='promotionfile'),
    re_path(r'promotion/(?P<fileid>' + reguuid + ')$', views.promotion_files, name='promotion_files'),  # direct url


    # student files (professionalskills)
    path('studentfile/<int:fileid>', views.student_files, name='studentfile'),  # object-id
    re_path(r'dist_(?P<distid>[0-9]+)/(?P<fileid>' + reguuid + ')$', views.student_files, name='student_files'),  # uri

    # capacity group images.
    path('capacitygroupimage/<int:fileid>', views.capacity_group_images, name='capacitygroupimage'),  # object-id
    re_path(r'capacitygroup_(?P<capid>[0-9]+)/(?P<fileid>' + reguuid + ')$', views.capacity_group_images, name='capacitygroupimages'),  # uri

    # capacity group images.
    path('masterprogramimage/<int:fileid>', views.master_program_images, name='masterprogramimage'),  # object-id
    re_path(r'masterprogram_(?P<capid>[0-9]+)/(?P<fileid>' + reguuid + ')$', views.master_program_images, name='masterprogramimages'),  # uri
]
