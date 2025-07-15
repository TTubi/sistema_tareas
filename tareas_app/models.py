import os
from django.conf import settings
from reportlab.pdfgen import canvas
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from reportlab.lib.utils import ImageReader

# CONSTANTES
PERFILES = [
    ('ingenieria', 'Ingeniería'),
    ('calidad', 'Calidad'),
    ('despacho', 'Despacho'),
    ('rrhh', 'RRHH'),
    ('produccion', 'Producción'),
    ('ppc', 'PPC'),
    ('administrador', 'Administrador'),

    # Perfiles hipotéticos solo para registro de trazabilidad
    ('armador', 'Armador'),
    ('soldador', 'Soldador'),
]

ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En progreso'),
        ('en_revision', 'En revision'),
        ('lista_para_pintar', 'Lista para pintar'),
        ('lista_para_despachar', 'Lista para despachar'),
        ('finalizada', 'Finalizada'),
        ('rechazada', 'Rechazada'), 
    )

SECTOR = (
        ('armado', 'Armado'),
        ('control_1', 'Control 1'),
        ('soldado', 'Soldado'),
        ('control_2', 'Control 2'),
        ('pintado', 'Pintado'),
        ('despachar', 'Despachar'),
        ('galvanizado', 'Galvanizado'),
        
)

# MODELOS

class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    perfil = models.CharField(max_length=50, choices=PERFILES)
    es_externo = models.BooleanField(default=False)

    @property
    def apellido(self):
        """Return last name from linked user if available."""
        return self.usuario.last_name if self.usuario else ""

    @property
    def nombre_completo(self):
        """Convenience property for templates."""
        if self.usuario and (self.usuario.first_name or self.usuario.last_name):
            return f"{self.usuario.first_name} {self.usuario.last_name}".strip()
        return self.nombre

    def __str__(self):
        return self.nombre
    
class AgenteExterno(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.CharField(max_length=100, blank=True, null=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre    

class OrdenDeTrabajo(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo_excel = models.FileField(upload_to='ordenes_excel/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
            return f"OT {self.id} - {self.nombre}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Primero guarda en la base de datos

        carpeta_ot = os.path.join(settings.MEDIA_ROOT, 'reportes', self.nombre.replace(' ', '_'))
        os.makedirs(carpeta_ot, exist_ok=True)

class Tarea(models.Model):
    titulo = models.CharField(max_length=100)
    sector = models.CharField(max_length=20, choices=SECTOR, blank=True, null=True)
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
    agente_externo = models.ForeignKey(AgenteExterno, null=True, blank=True, on_delete=models.SET_NULL)

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


def avanzar_tarea(tarea, accion, empleado, destino_final=None):
    # Etapa 1 → Asignación de Armador
    if tarea.estado == 'pendiente' and accion == 'asignar_armador':
        tarea.estado = 'en_progreso'
        tarea.sector = 'armado'

    # Etapa 1 finalizada → Enviar a CONTROL 1
    elif tarea.estado == 'en_progreso' and tarea.sector == 'armado' and accion == 'enviar_a_calidad':
        tarea.estado = 'en_revision'
        tarea.sector = 'control_1'

    # Etapa 2 → CONTROL 1 aprueba
    elif tarea.estado == 'en_revision' and tarea.sector == 'control_1' and accion == 'aprobado_por_calidad':
        tarea.estado = 'pendiente'
        tarea.sector = 'soldado'

    # Etapa 2 → CONTROL 1 rechaza
    elif tarea.estado == 'en_revision' and tarea.sector == 'control_1' and accion == 'rechazado_por_calidad':
        tarea.estado = 'pendiente'
        tarea.sector = 'armado'

    # Etapa 3 → SOLDADO inicia trabajo
    elif tarea.estado == 'pendiente' and tarea.sector == 'soldado' and accion == 'asignar_soldador':
        tarea.estado = 'en_progreso'

    # Etapa 3 finalizada → Enviar a CONTROL 2
    elif tarea.estado == 'en_progreso' and tarea.sector == 'soldado' and accion == 'enviar_a_calidad':
        tarea.estado = 'en_revision'
        tarea.sector = 'control_2'

    # Etapa 4 → CONTROL 2 aprueba y envía a destino
    elif tarea.estado == 'en_revision' and tarea.sector == 'control_2' and accion == 'segunda_aprobacion':
        if destino_final == 'pintado':
            tarea.estado = 'lista_para_pintar'
            tarea.sector = 'pintado'
        elif destino_final == 'despachar':
            tarea.estado = 'lista_para_despachar'
            tarea.sector = 'despachar'
        elif destino_final == 'galvanizado':
            tarea.estado = 'galvanizado'
            tarea.sector = 'galvanizado'

    # Etapa post-galvanizado → vuelve a control
    elif tarea.estado == 'galvanizado':
        tarea.estado = 'en_revision'
        tarea.sector = 'control_2'

    # Etapa 4 → CONTROL 2 rechaza
    elif tarea.estado == 'en_revision' and tarea.sector == 'control_2' and accion == 'rechazado_por_calidad':
        tarea.estado = 'pendiente'
        tarea.sector = 'soldado'

    # Etapa 5 → PINTADO finalizado
    elif tarea.estado == 'lista_para_pintar' and tarea.sector == 'pintado' and accion == 'pintado_finalizado':
        tarea.estado = 'lista_para_despachar'
        tarea.sector = 'despachar'

    # Etapa 6 → DESPACHO finaliza tarea
    elif tarea.estado == 'lista_para_despachar' and tarea.sector == 'despachar' and accion == 'marcar_finalizada':
        tarea.estado = 'finalizada'


    tarea.save()

    def tarea_destino_final(tarea):
        destino = tarea.destino_final  # este valor debería llegar del formulario
        if destino == 'pintado':
            return {'estado': 'lista_para_pintar', 'sector': 'pintado'}
        elif destino == 'despacho':
            return {'estado': 'lista_para_despachar', 'sector': 'despacho'}
        elif destino == 'galvanizado':
            return {'estado': 'galvanizado', 'sector': 'galvanizado'}



class Movimiento(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='movimientos')
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarea.titulo} - {self.estado_anterior} ➜ {self.estado_nuevo} ({self.fecha_hora})"

    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')


class Comentario(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(Empleado, null=True, on_delete=models.SET_NULL)
    texto = models.TextField()
    imagen = models.ImageField(upload_to="comentarios/", null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        autor_nombre = self.autor.nombre if self.autor else "Anonimo"
        return f"{autor_nombre}: {self.texto[:20]}"





