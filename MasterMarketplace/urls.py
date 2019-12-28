"""
MasterMarketplace URL Configuration

"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.conf import settings
from django.views.generic.base import RedirectView

admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    # path('osiris/', include('osiris.urls')),
    path('', include('index.urls')),
    path('accesscontrol/', include('accesscontrol.urls')),
    path('admin/', admin.site.urls),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('api/', include('api.urls')),
    path('download/', include('download.urls')),
    path('godpowers/', include('godpowers.urls')),
    path('impersonate/', include('impersonate.urls')),
    path('js_error_hook/', include('django_js_error_hook.urls')),
    path('projects/', include('projects.urls')),
    path('registration/', include('registration.urls')),
    path('students/', include('students.urls')),
    path('studyguide/', include('studyguide.urls')),
    path('support/', include('support.urls')),
    path('tracking/', include('tracking.urls')),
    path('two_factor/', include('two_factor_custom.urls')),
    path('shen/', include('shen_ring.urls')),

]

if settings.DEBUG and False:
    import debug_toolbar

    urlpatterns = [
        path('debug/', include(debug_toolbar.urls)),

    ] + urlpatterns

# static download path, for unprotected downloads. Not used.
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers.
handler400 = 'index.views.error400'
handler404 = 'index.views.error404'
handler403 = 'index.views.error403'
handler500 = 'index.views.error500'
