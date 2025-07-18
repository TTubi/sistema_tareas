# Generated by Django 5.2.1 on 2025-06-27 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tareas_app', '0007_ordendetrabajo_tarea_orden'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarea',
            name='cantidad',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tarea',
            name='enominacion',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='tarea',
            name='estructura',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='tarea',
            name='peso_total',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tarea',
            name='peso_unitario',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tarea',
            name='plano_codigo',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='tarea',
            name='posicion',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
