import sys
sys.path.append('..')

from django.conf.urls.defaults import *
from django.conf import settings

import general.admin_auth

from ParkingPermit.views import stats, non_credentialed_register

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^CampusSecurity/', include('CampusSecurity.foo.urls')),
    #('^denied/$',denied),
    #(r'^conference/', conference),
    #(r'^accounts/login/$', 'django.contrib.auth.views.login', 
    #    {'template_name': 'login.html'}),
    #(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^stats/$', stats),
    (r'^nocred/$', non_credentialed_register),
    # Uncomment the next line to enable the admin:
    (r'^', include(admin.site.urls)),
)

if settings.DEBUG:
    # Make Django serve static files.  Not applicable for production.
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root': settings.MEDIA_ROOT}),
    )

