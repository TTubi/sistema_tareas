# Generated by Django 5.2.1 on 2025-07-25 17:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tareas_app', '0019_tarea_operarios'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimiento',
            name='hecho_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tareas_app.empleado'),
        ),
    ]
