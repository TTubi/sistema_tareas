#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

echo "
from django.contrib.auth import get_user_model
from tareas_app.models import Empleado
User = get_user_model()
user = User.objects.get(username='admin')
if not Empleado.objects.filter(usuario=user).exists():
    Empleado.objects.create(
        usuario=user,
        nombre='Administrador',
        apellido='Principal',
        perfil='administrador'
    )
" | python manage.py shell