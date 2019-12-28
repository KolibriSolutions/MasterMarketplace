## DJANGO SETTTINGS

## 01-marketplace.py
## Settings specific for this marketplace instance


import os

try:
    from MasterMarketplace.config.secret import SECRET_KEY_IMPORT
except:
    from MasterMarketplace.secret import SECRET_KEY_IMPORT

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DJANGO settings
##################

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY_IMPORT

SETTINGS_DIR = 'MasterMarketplace'

CONTACT_EMAIL = 'mastermarketplace@tue.nl'
DEV_EMAIL = 'mastermarketplace@kolibrisolutions.nl'

SUPPORT_ROLE = 'academic advisor'
SUPPORT_NAME = 'Harald van den Meerendonk'
SUPPORT_EMAIL = 'Academic.Advisor.MEE@tue.nl'
# SUPPORT_EMAIL = 'H.J.A.v.d.Meerendonk@tue.nl'

ADMINS = [('Kolibri Solutions', DEV_EMAIL)]
MANAGERS = ADMINS  # to mail broken links to, not used now.

NAME_CODE = 'MasterMarketplace'
NAME_PRETTY = 'Master Marketplace'

TESTING = False

# General settings for the projects
####################################
MAX_NUM_APPLICATIONS = 20  # number of applications a student can have.
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # max size of any uploaded file 10MB. This limit should be lower than the NGINX limit
MAXAGESHARELINK = 60 * 60 * 24 * 7 * 104  # two year

ALLOWED_PROJECT_ATTACHMENTS = ['pdf']  # allowed files for project attachments
ALLOWED_PROJECT_IMAGES = ['jpg', 'jpeg', 'png', 'bmp', 'gif']  # allowed files as project images.
MARKDOWN_ALLOWED_IMAGES_TYPES = ALLOWED_PROJECT_IMAGES
ALLOWED_PROMOTION_LOGOS = ALLOWED_PROJECT_IMAGES  # allowed files as promotion logo
ALLOWED_PUBLIC_FILES = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'odt', 'ods', 'odp',
                        'ppt', 'pptx', 'tex', 'txt', 'rtf']
# to check when a user is staff on saml login.
STAFF_EMAIL_DOMAINS = ['tue.nl', ]
# to check whether a email address can be used to add an assistant
ALLOWED_PROJECT_ASSISTANT_DOMAINS = STAFF_EMAIL_DOMAINS
# email domains allowed in access control objects
STUDENT_EMAIL_DOMAINS = ['student.tue.nl', ]
ALLOWED_ACCESSCONTROL_DOMAINS = STUDENT_EMAIL_DOMAINS

# How long to cache models that are assumed static. (Group types, timeslots, timphases)
STATIC_OBJECT_CACHE_DURATION = 15 * 60  # 15 minutes.

# regex checks
EMAILREGEXCHECK = '(^[a-zA-Z0-9]{1}[a-zA-Z0-9_.+-~]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'  # regex that checks for email.
# COURSECODEREGEX = r"\b[0-9]\w{4}[0-9]\b|\b[0-9]\w{3}[0-9]\b|\b[0-9]\w{2}[0-9]\b|\w{2}\b[0-9]{3}\b"  # number, 2-4 letters, number
COURSECODEREGEX = r"\b([A-z]|[0-9]){3,7}\b"
LINKREGEX = r'\[([^\[]+)\]\(([^\)]+)\)'

APPROVAL_STUDY_PACKAGE_FORM_XLSX_LINK = "https://assets.studiegids.tue.nl/fileadmin/content/Faculteit_EE/Graduate_School/Masteropleidingen/EE-Approval_study_package_form_MSc_study_program.xlsx"

INSTALLED_APPS = [
    'accesscontrol.apps.AccesscontrolConfig',
    'download.apps.DownloadConfig',
    'godpowers.apps.GodpowersConfig',
    'index.apps.IndexConfig',
    'projects.apps.ProjectsConfig',
    'registration.apps.RegistrationConfig',
    'students.apps.StudentsConfig',
    'studyguide.apps.StudyguideConfig',
    'support.apps.SupportConfig',
    'templates.apps.TemplatesConfig',
    'timeline.apps.TimelineConfig',
    'tracking.apps.TrackingConfig',
    'two_factor_custom.apps.TwoFactorCustomConfig',
    'virustotal.apps.VirustotalConfig',
    'shen_ring.apps.ShenRingConfig',

    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',

    'channels',
    'csp',
    'impersonate',
    'openpyxl',
    'sendfile',
    'two_factor',
    'django_js_error_hook',
]
