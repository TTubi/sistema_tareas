import os
from django.conf import settings
from reportlab.pdfgen import canvas
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from reportlab.lib.utils import ImageReader
import cloudinary.uploader

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
        ('pendiente','Pendiente'),
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
    empresa = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.nombre    

class OrdenDeTrabajo(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo_excel = models.FileField(upload_to='ordenes_excel/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)
    finalizada = models.BooleanField(default=False)

    def __str__(self):
            return f"OT {self.id} - {self.nombre}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Primero guarda en la base de datos

        carpeta_ot = os.path.join(settings.MEDIA_ROOT, 'reportes', self.nombre.replace(' ', '_'))
        os.makedirs(carpeta_ot, exist_ok=True)

class Tarea(models.Model):
    titulo = models.CharField(max_length=100)
    sector = models.CharField(max_length=30, choices=SECTOR, default='pendiente')
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
    operarios = models.ManyToManyField(Empleado, related_name='tareas_operadas', blank=True)
    pdf_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        
        if self.pk:
            tarea_anterior = Tarea.objects.get(pk=self.pk)
            if tarea_anterior.estado != self.estado:
                if not self.movimientos.filter(
                estado_anterior=tarea_anterior.estado,
                estado_nuevo=self.estado,
                fecha_hora__date=timezone.now().date()
                ).exists():
                    Movimiento.objects.create(
                    tarea=self,
                    estado_anterior=tarea_anterior.estado,
                    estado_nuevo=self.estado
                    )

                
                if self.estado == 'finalizada':
                    self.generar_pdf()

        super().save(*args, **kwargs)


    def generar_pdf(self):
        if not self.orden:
            return

        carpeta = os.path.join(settings.MEDIA_ROOT, 'reportes', f"OT_{self.orden.id}")
        os.makedirs(carpeta, exist_ok=True)

        nombre_pdf = f"{self.titulo.replace(' ', '_')}.pdf"
        archivo_pdf = os.path.join(carpeta, nombre_pdf)
        c = canvas.Canvas(archivo_pdf)
        c.setFont("Helvetica", 12)

        y = 800
        def draw_line(text):
            nonlocal y
            c.drawString(100, y, text)
            y -= 20
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800

        draw_line(f"Tarea: {self.titulo}")
        draw_line(f"Descripción: {self.descripcion}")

    # === Operarios ===
        if hasattr(self, 'operarios'):
            operarios = self.operarios.all()
            if operarios.exists():
                texto_op = ", ".join([f"{o.nombre} {o.apellido} ({o.perfil})" for o in operarios])
            else:
                texto_op = "Sin operarios registrados"
        else:
            texto_op = f"{self.asignado_a}"
        draw_line(f"Operarios: {texto_op}")

        draw_line(f"Fecha creación: {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}")
        if hasattr(self, 'fecha_finalizacion') and self.fecha_finalizacion:
            draw_line(f"Fecha finalización: {self.fecha_finalizacion.strftime('%Y-%m-%d %H:%M')}")

        draw_line("")
        draw_line("=== Detalle de fabricación ===")
        draw_line(f"Plano: {self.plano_codigo}")
        draw_line(f"Posición: {self.posicion}")
        draw_line(f"Estructura: {self.estructura}")
        draw_line(f"Denominación: {self.denominacion}")
        draw_line(f"Cantidad: {self.cantidad}")
        draw_line(f"Peso Unitario: {self.peso_unitario} kg")
        draw_line(f"Peso Total: {self.peso_total} kg")

        draw_line("")
        draw_line("=== Movimientos ===")

        for mov in self.movimientos.order_by('fecha_hora'):
            linea = f"{mov.fecha_hora.strftime('%Y-%m-%d %H:%M')} - "

            if mov.estado_anterior != mov.estado_nuevo:
                linea += f"{mov.estado_anterior} ➜ {mov.estado_nuevo}"
            else:
                linea += f"{mov.estado_nuevo}"

            if hasattr(mov, 'tipo') and mov.tipo == 'asignacion' and mov.detalles:
                linea += f" - {mov.detalles}"

            if mov.estado_nuevo == 'en_revision' and mov.hecho_por and mov.hecho_por.perfil == 'calidad':
                linea += f" - Controlado por: {mov.hecho_por.nombre} {mov.hecho_por.apellido} ({mov.hecho_por.perfil})"

            if mov.estado_nuevo == 'finalizada' and mov.estado_anterior == 'lista_para_despachar':
                if mov.hecho_por:
                    linea += f" - Despachado por: {mov.hecho_por.nombre} {mov.hecho_por.apellido}"
                else:
                    linea += f" - Despachado por: No registrado"

            draw_line(linea)

        draw_line("")
        draw_line("=== Comentarios ===")
        for comentario in self.comentarios.order_by('fecha_creacion'):
            autor = comentario.autor.nombre if comentario.autor else "Anónimo"
            texto = comentario.texto.replace('\n', ' ')
            draw_line(f"[{comentario.fecha_creacion.strftime('%Y-%m-%d %H:%M')}] {autor}: {texto[:100]}")

        # 👇 Mostrar imagen si hay
            if comentario.imagen and comentario.imagen.path:
                try:
                    img = ImageReader(comentario.imagen.path)
                    c.drawImage(img, 120, y - 150, width=200, height=150)
                    y -= 170
                    if y < 100:
                        c.showPage()
                        c.setFont("Helvetica", 12)
                        y = 800
                except:
                    draw_line("⚠️ Error al cargar imagen.")

        c.save()
        try:
            response = cloudinary.uploader.upload(archivo_pdf, resource_type="raw")
            url_pdf = response['secure_url']
            print(f"PDF subido correctamente a: {url_pdf}")
            Tarea.objects.filter(id=self.id).update(pdf_url=url_pdf)
        except Exception as e:
            print("Error al subir PDF a Cloudinary:", e)
            
            



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
        tarea.estado = 'rechazado'
        tarea.sector = 'armado'

    elif tarea.estado == 'rechazado' and tarea.sector == 'armado' and accion == 'enviar_a_calidad':
        tarea.estado = 'en_revision'
        tarea.sector = 'control_1'

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
        tarea.estado = 'rechazado'
        tarea.sector = 'soldado'

    elif tarea.estado == 'rechazado' and tarea.sector == 'soldado' and accion == 'enviar_a_calidad':
        tarea.estado = 'en_revision'
        tarea.sector = 'control_2'

    # Etapa 5 → PINTADO finalizado
    elif tarea.estado == 'lista_para_pintar' and tarea.sector == 'pintado' and accion == 'pintado_finalizado':
        tarea.estado = 'lista_para_despachar'
        tarea.sector = 'despachar'

    # Etapa 6 → DESPACHO finaliza tarea
    elif tarea.estado == 'lista_para_despachar' and tarea.sector == 'despachar' and accion == 'marcar_finalizada':
        tarea.estado = 'finalizada'

        Movimiento.objects.create(
            tarea=tarea,
            estado_anterior='lista_para_despachar',
            estado_nuevo='finalizada',
            hecho_por=empleado,
            detalles="Tarea despachada"
        )

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
    hecho_por = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)
    detalles = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)

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





