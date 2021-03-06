# MIDDLEWARE.remove("htmlmin.middleware.HtmlMinifyMiddleware")

# to allow websockets in CSP over plain http
CSP_CONNECT_SRC = ("'self'", "ws://localhost:*")  # websockets and ajax. Make sure wss:// is set and not ws://.
#
# INSTALLED_APPS.append('debug_toolbar')
# MIDDLEWARE.insert(0,'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS='127.0.0.1'

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    # 'debug_toolbar.panels.settings.SettingsPanel',
    # 'debug_toolbar.panels.headers.HeadersPanel',
    # 'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    # 'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    # 'debug_toolbar.panels.templates.TemplatesPanel',
    # 'debug_toolbar.panels.cache.CachePanel',
    # 'debug_toolbar.panels.signals.SignalsPanel',
    # 'debug_toolbar.panels.logging.LoggingPanel',
    # 'debug_toolbar.panels.redirects.RedirectsPanel',
]
DEBUG_TOOLBAR_CONFIG = {
    'JQUERY_URL': None,

}
# CSP_DEFAULT_SRC = None
# CSP_SCRIPT_SRC = None
# CSP_STYLE_SRC = None
# CSP_IMG_SRC = None  # base64 images are used by lightbox
# CSP_CONNECT_SRC = None  # websockets and ajax. Make sure wss:// is set and not ws://.
# CSP_BASE_URI = None
# CSP_FRAME_ANCESTORS = None
# CSP_FORM_ACTION = None
