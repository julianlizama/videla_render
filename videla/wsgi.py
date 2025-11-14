"""
WSGI config for videla project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "videla.settings")

# Ejecutar la creación automática de superusuario (solo en Render)
try:
    from .create_superuser import run
    run()
except Exception as e:
    print("\n=== Error creando superusuario automáticamente ===")
    print(e)
    print("=== Fin del error ===\n")

application = get_wsgi_application()
