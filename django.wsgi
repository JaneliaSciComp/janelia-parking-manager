#This is used by mod_wsgi to run the project
#http://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/

import os
import sys
paths = ('/opt/DjangoProjects','/opt/DjangoProjects/Parking') #production 
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'Parking.settings'
os.environ['PYTHON_EGG_CACHE'] = '/opt/tmp'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

