import os
from django.conf import settings
from reportlab.pdfgen import canvas
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

# CONSTANTES
PERFILES = (
    ('operario', 'Operario'),
    ('controlador', 'Controlador'),
    ('encargado', 'Encargado'),
    ('admin', 'Administrador'),
)

ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En progreso'),
        ('en_revision', 'En revision'),
        ('finalizada', 'Finalizada'),
        ('rechazada', 'Rechazada'),
    )

# MODELOS

class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    perfil = models.CharField(max_length=20, choices=PERFILES)


    def __str__(self):
        return f"{self.usuario.username} ({self.perfil})"

class OrdenDeTrabajo(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo_excel = models.FileField(upload_to='ordenes_excel/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"OT {self.id} - {self.nombre}"

class Tarea(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    asignado_a = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name="tareas_asignadas")
    creada_por = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    plano = models.ImageField(upload_to='planos/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    orden = models.ForeignKey(OrdenDeTrabajo, related_name='tareas', on_delete=models.CASCADE, null=True, blank=True)
    estructura = models.CharField(max_length=100, blank=True)
    plano_codigo = models.CharField(max_length=50, blank=True)
    posicion = models.CharField(max_length=50, blank=True)
    denominacion = models.CharField(max_length=100, blank=True)
    cantidad = models.IntegerField(null=True, blank=True)
    peso_unitario = models.FloatField(null=True, blank=True)
    peso_total = models.FloatField(null=True, blank=True)

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

    y = 800
    c.drawString(100, y, f"Tarea: {self.titulo}")
    y -= 20
    c.drawString(100, y, f"Descripción: {self.descripcion}")
    y -= 20
    c.drawString(100, y, f"Asignado a: {self.asignado_a}")
    y -= 20
    c.drawString(100, y, f"Creada por: {self.creada_por}")
    y -= 20
    c.drawString(100, y, f"Fecha creación: {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}")
    y -= 20
    c.drawString(100, y, f"Fecha finalización: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 40

    c.drawString(100, y, "=== Detalle de fabricación ===")
    y -= 20
    c.drawString(100, y, f"Plano: {self.plano_codigo}")
    y -= 20
    c.drawString(100, y, f"Posición: {self.posicion}")
    y -= 20
    c.drawString(100, y, f"Denominación: {self.denominacion}")
    y -= 20
    c.drawString(100, y, f"Cantidad: {self.cantidad}")
    y -= 20
    c.drawString(100, y, f"Peso Unitario: {self.peso_unitario} kg")
    y -= 20
    c.drawString(100, y, f"Peso Total: {self.peso_total} kg")
    y -= 20
    c.drawString(100, y, f"Construye en: {self.construye_en}")
    y -= 20
    c.drawString(100, y, f"Clasificación: {self.clasificacion}")
    y -= 40

    # Verificar si hay espacio suficiente para Movimientos
    if y < 150:
        c.showPage()
        c.setFont("Helvetica", 12)
        y = 800

    c.drawString(100, y, "=== Movimientos ===")
    y -= 20
    for mov in self.movimientos.all():
        if y < 100:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 800
        c.drawString(120, y, f"{mov.fecha_hora.strftime('%Y-%m-%d %H:%M')} - {mov.estado_anterior} ➜ {mov.estado_nuevo}")
        y -= 20

    # Agregar imagen del plano si existe
    if self.plano and self.plano.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            plano_path = os.path.join(settings.MEDIA_ROOT, self.plano.name)
            c.showPage()
            c.setFont("Helvetica", 12)
            c.drawString(100, 800, "Plano adjunto:")
            c.drawImage(ImageReader(plano_path), x=100, y=400, width=400, height=300, preserveAspectRatio=True)
        except Exception as e:
            c.drawString(100, 780, f"Error al cargar plano: {e}")

    c.save()



class Movimiento(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='movimientos')
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarea.titulo} - {self.estado_anterior} ➜ {self.estado_nuevo} ({self.fecha_hora})"

    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')




