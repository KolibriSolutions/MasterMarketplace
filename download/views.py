from os import path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from sendfile import sendfile

from general_model import get_ext
from general_view import get_grouptype
from projects.models import ProjectAttachment, ProjectImage, Project
from students.models import StudentFile
from studyguide.models import CapacityGroupImage, MasterProgramImage
from support.models import Promotion

"""
Uploads go to /media/ directory
Download links point to /download
Downloads can either be by file path (old way, as if we're using a public file storage pool). Used by editfile widget
or as a primary key of the object the file belongs to (new way). Used in all templates.
"""


# @login_required
# def PublicFiles(request, fileid):
#     """
#     Public files, uploaded by type3, viewable on index.html, model in support-app
#     Cannot be viewed via edit-files, because access via URL is not supported. Only access via file id.
#     :param request:
#     :param fileid: The ID of the public file to download.
#     :return: file download
#     """
#     #first try PK, then filename
#     #try:
#     #    obj = PublicFile.objects.get(id=fileid)
#     #except:
#     #    obj = get_object_or_404(PublicFile, File='public_files/'+fileid)
#
#     obj = get_object_or_404(PublicFile, id=fileid)
#     return sendfile(request, obj.File.path, attachment=True, attachment_filename=obj.OriginalName)


def project_files(request, fileid, project_id=None, ty=None):
    """
    project files, attachments or images, viewable on project details, model in projects-app
    Because projects images and attachments are separate models, but are stored in the same folder, the ID is not
    unique, therefore only the UUID is possible to get the file.
    Mode 1: (old) projectid gives the folder to search in, fileid is the filename (an UUID)
    Mode 2: (new) ty is either "a" or "i" to refer to image or attachment and fileid is the ID (pk) of-
     the corresponding model
    When the file is an image, it is send inline, otherwise it is send as attachment.

    :param request:
    :param fileid: id of the project file.
    :param project_id: id of the project, corresponds to directory name appendix.
    :param ty: type, image or attachment
    :return: file download
    """
    if not request.user.is_authenticated:
        # allow anonymous users when viewing from a sharelink
        # make sure referrerpolicy is set on links, otherwise HTTP_REFERER might not be available.
        # https: // bugs.chromium.org / p / chromium / issues / detail?id = 455987
        if "HTTP_REFERER" in request.META:
            ref = request.META["HTTP_REFERER"].split('/')
            if 'share' in ref:  # url  /api/share/<sharetoken>/
                # check if sharetoken is valid. Same as in api.views
                try:
                    pk = signing.loads(ref[-2], max_age=settings.MAXAGESHARELINK)
                except signing.SignatureExpired:
                    raise PermissionDenied('Not allowed!')
                except signing.BadSignature:
                    raise PermissionDenied('Not allowed!')
                if not Project.objects.filter(pk=pk).exists():
                    # a check whether this image/attachment belongs to this project would be better
                    # but is more difficult.
                    raise PermissionDenied('Not allowed!')
                pass  # anonymous user viewing a valid share link
            else:
                raise PermissionDenied('Not allowed!')  # random referred
        else:  # direct access to file
            raise PermissionDenied('Not allowed!')

    # first try filename as image, then as attachment
    if project_id:  # via a project id and a filename (UUID) as fileid, the old way
        ext = get_ext(fileid)
        if ext in settings.ALLOWED_PROJECT_IMAGES:
            obj = get_object_or_404(ProjectImage, File='project_{}/{}'.format(project_id, fileid))
            return sendfile(request, obj.File.path, attachment=False)  # serve inline
        elif ext in settings.ALLOWED_PROJECT_ATTACHMENTS:
            obj = get_object_or_404(ProjectAttachment, File='project_{}/{}'.format(project_id, fileid))
            return sendfile(request, obj.File.path, attachment=True, attachment_filename=obj.OriginalName)
        else:
            raise PermissionDenied("File extension not allowed.")
    elif ty:  # by specifying image or attachement and a ID (pk) as fileid, the new way
        if ty == "a":  # attachment, like pdf
            obj = get_object_or_404(ProjectAttachment, id=fileid)
            return sendfile(request, obj.File.path, attachment=True, attachment_filename=obj.OriginalName)
        elif ty == "i":  # image
            obj = get_object_or_404(ProjectImage, id=fileid)
            return sendfile(request, obj.File.path)
        else:
            raise PermissionDenied("Invalid request.")
    else:
        raise PermissionDenied("Invalid request.")


@login_required
def promotion_files(request, fileid):
    """

    :param request:
    :param fileid: object pk or file uuid
    :return:
    """
    try:
        obj = Promotion.objects.get(id=fileid)
    except:
        obj = get_object_or_404(Promotion, File='promotion/{}'.format(fileid))
    return sendfile(request, obj.File.path)


@login_required
def student_files(request, fileid, distid=''):
    """
    Student file, uploaded by student as
    Responsible and assistant of student can view files.
    Student itself can view its own files

    :param request:
    :param fileid: id of the student file.
    :param distid: id of the distribution of the student.
    :return:
    """
    # first try PK, then filename
    try:
        obj = StudentFile.objects.get(id=fileid)
    except (StudentFile.DoesNotExist, ValueError):
        # accessed by distribution, then by filename
        obj = get_object_or_404(StudentFile, File='dist_{}/{}'.format(distid, fileid))

    if get_grouptype("studyadvisors") in request.user.groups.all() \
            or obj.Distribution.Project.ResponsibleStaff == request.user \
            or request.user in obj.Distribution.Project.Assistants.all() \
            or obj.Distribution.Student == request.user:
        # Allowed to view this file
        return sendfile(request, obj.File.path, attachment=True, attachment_filename=obj.OriginalName)
    else:
        # not allowed
        raise PermissionDenied("You are not allowed to view this file.")

@login_required
def capacity_group_images(request, fileid, capid=''):
    """

    :param request:
    :param fileid: id of the image.
    :param capid: id of the capacitygroup.
    :return:
    """
    # first try PK, then filename
    try:
        obj = CapacityGroupImage.objects.get(id=fileid)
    except (CapacityGroupImage.DoesNotExist, ValueError):
        # accessed by distribution, then by filename
        obj = get_object_or_404(CapacityGroupImage, File='capacitygroup_{}/{}'.format(capid, fileid))
    return sendfile(request, obj.File.path, attachment=True, attachment_filename=obj.OriginalName)


@login_required
def master_program_images(request, fileid, capid=''):
    """

    :param request:
    :param fileid: id of the image.
    :param capid: id of the master program.
    :return:
    """
    # first try PK, then filename
    try:
        obj = MasterProgramImage.objects.get(id=fileid)
    except (MasterProgramImage.DoesNotExist, ValueError):
        # accessed by distribution, then by filename
        obj = get_object_or_404(MasterProgramImage, File='masterprogram_{}/{}'.format(capid, fileid))
    return sendfile(request, obj.File.path, attachment=True, attachment_filename=obj.OriginalName)


def markdown_file_download(request, file_name):
    """
    Function to return images uploaded by markdown EasyMDE. Not stored in object/database, only file is saved.

    :param request:
    :param file_name: The name of the file
    :return: file inline
    """
    file_path = path.join(settings.MEDIA_ROOT, settings.MARKDOWN_IMAGE_UPLOAD_FOLDER, file_name)
    return sendfile(request, file_path, attachment=False)
