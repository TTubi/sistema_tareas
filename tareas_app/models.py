import os
from django.conf import settings
from reportlab.pdfgen import canvas
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

PERFILES = (
    ('operario', 'Operario'),
    ('controlador', 'Controlador'),
    ('encargado', 'Encargado'),
    ('admin', 'Administrador'),
)


class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    perfil = models.CharField(max_length=20, choices=PERFILES)


    def __str__(self):
        return f"{self.usuario.username} ({self.perfil})"

class Tarea(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    asignado_a = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name="tareas_asignadas")
    creada_por = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    plano = models.ImageField(upload_to='planos/', null=True, blank=True)

    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En progreso'),
        ('en_revision', 'En revision'),
        ('finalizada', 'Finalizada'),
        ('rechazada', 'Rechazada'),
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def save(self, *args, **kwargs):
        # Comprobar si el estado cambió
        if self.pk:
            tarea_anterior = Tarea.objects.get(pk=self.pk)
            if tarea_anterior.estado != self.estado:
                # Guardar movimiento
                Movimiento.objects.create(
                    tarea=self,
                    estado_anterior=tarea_anterior.estado,
                    estado_nuevo=self.estado
                )

                # Si pasó a finalizada, crear PDF
                if self.estado == 'finalizada':
                    self.generar_pdf()

        super().save(*args, **kwargs)

    def generar_pdf(self):
        carpeta = os.path.join(settings.MEDIA_ROOT, 'reportes')
        os.makedirs(carpeta, exist_ok=True)

        archivo_pdf = os.path.join(carpeta, f"{self.titulo.replace(' ', '_')}.pdf")
        c = canvas.Canvas(archivo_pdf)
        c.setFont("Helvetica", 12)

        c.drawString(100, 800, f"Tarea: {self.titulo}")
        c.drawString(100, 780, f"Descripción: {self.descripcion}")
        c.drawString(100, 760, f"Asignado a: {self.asignado_a}")
        c.drawString(100, 740, f"Creada por: {self.creada_por}")
        c.drawString(100, 720, f"Fecha creación: {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}")
        c.drawString(100, 700, f"Fecha finalización: {timezone.now().strftime('%Y-%m-%d %H:%M')}")

        y = 680
        c.drawString(100, y, "Movimientos:")
        for mov in self.movimientos.all():
            y -= 20
            c.drawString(120, y, f"{mov.fecha_hora.strftime('%Y-%m-%d %H:%M')} - {mov.estado_anterior} ➜ {mov.estado_nuevo}")

        c.save()


class Movimiento(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='movimientos')
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarea.titulo} - {self.estado_anterior} ➜ {self.estado_nuevo} ({self.fecha_hora})"

    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En progreso'),
        ('en_revision', 'En revision'),
        ('finalizada', 'Finalizada'),
        ('rechazada', 'Rechazada'),
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')




