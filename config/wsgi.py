"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

# Add venv bin to PATH so ffmpeg can be found when running under mod_wsgi
venv_bin = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'venv', 'bin')
if venv_bin not in os.environ.get('PATH', ''):
    os.environ['PATH'] = f"{venv_bin}:{os.environ.get('PATH', '')}"

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

application = get_wsgi_application()
