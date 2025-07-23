from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Tarea, Empleado, OrdenDeTrabajo, AgenteExterno, Comentario, PERFILES, avanzar_tarea, ESTADOS
from django.contrib.auth.models import User
from .forms import (
    TareaForm,
    OrdenDeTrabajoForm,
    AgenteExternoForm,
    AsignarAgenteExternoForm,
    ComentarioForm,
)
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.views import LoginView
import pandas as pd
import numpy as np

def es_admin(empleado):
    return empleado.perfil == 'administrador'

def puede_asignar(empleado):
    return empleado.perfil in ['administrador', 'produccion', 'ingenieria']

def puede_ver_avances(empleado):
    return empleado.perfil in ['administrador', 'ppc', 'produccion', 'calidad', 'despacho', 'ingenieria', 'rrhh']

def es_calidad(empleado):
    return empleado.perfil == 'calidad'

def es_operario(empleado):
    return empleado.perfil in ['armador', 'soldador',]

def es_rrhh(empleado):
    return empleado.perfil in ['rrhh']

def es_admin_o_ingenieria(empleado):
    return hasattr(empleado, 'empleado') and empleado.empleado.perfil in ['ingenieria', 'administrador']

class CustomLoginView(LoginView):
    template_name = 'login.html'  

    def form_valid(self, form):
        response = super().form_valid(form)
        remember_me = self.request.POST.get('recordarme')

        if not remember_me:
            # Cierra sesión al cerrar el navegador
            self.request.session.set_expiry(0)
        else:
            # Sesión persiste 30 días
            self.request.session.set_expiry(60 * 60 * 24 * 30)

        return response
@login_required
def redirect_por_perfil(request):
    return redirect('lista_ordenes_trabajo')

@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['administrador', 'rrhh'])
def lista_usuarios_completa(request):
    # Personal de taller
    perfiles_taller = ['soldador', 'armador', 'calidad', 'despacho', 'produccion']
    usuarios_taller = Empleado.objects.filter(perfil__in=perfiles_taller, es_externo=False)

    # Mensuales
    perfiles_mensuales = ['ppc', 'rrhh', 'ingenieria', 'administrador']
    usuarios_mensuales = Empleado.objects.filter(perfil__in=perfiles_mensuales, es_externo=False)

    # Agentes externos
    agentes_externos = AgenteExterno.objects.all()

    context = {
        'usuarios_taller': usuarios_taller,
        'usuarios_mensuales': usuarios_mensuales,
        'agentes_externos': agentes_externos,
    }

    return render(request, 'usuarios/lista_usuarios_completa.html', context)


def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if request.method == 'POST':
        usuario.first_name = request.POST['first_name']
        usuario.last_name = request.POST['last_name']
        usuario.email = request.POST['email']
        usuario.save()

        usuario.empleado.perfil = request.POST['perfil']
        usuario.empleado.save()

        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('lista_usuarios')
    
        if request.method == 'POST':
            user.username = request.POST.get('username') if perfil not in ['Soldador', 'Armador'] else user.username
    
            password = request.POST.get('password')
        if password and perfil not in ['Soldador', 'Armador']:
            user.set_password(password)

    # ... actualizás otros campos ...
            user.save()

    return render(request, 'usuarios/editar_usuario.html', {
        'usuario': usuario,
        'perfiles': PERFILES
    })

def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('lista_usuarios')  # Asegurate que esta URL exista

    return render(request, 'usuarios/eliminar_usuario.html', {
        'usuario': usuario
    })


@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['rrhh', 'administrador'])
def editar_personal_taller(request, id):
    personal = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':
        personal.nombre = request.POST.get('nombre')
        personal.perfil = request.POST.get('perfil')
        personal.save()
        messages.success(request, "Personal actualizado correctamente.")
        return redirect('lista_usuarios')

    return render(request, 'usuarios/editar_personal_taller.html', {'personal': personal})


@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['rrhh', 'administrador'])
def eliminar_personal_taller(request, id):
    personal = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':
        personal.delete()
        messages.success(request, "Personal eliminado correctamente.")
        return redirect('lista_usuarios')

    return render(request, 'usuarios/eliminar_personal_taller.html', {'personal': personal})

@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['rrhh', 'administrador'])
def editar_agente_externo(request, id):
    agente = get_object_or_404(AgenteExterno, id=id)

    if request.method == 'POST':
        agente.nombre = request.POST.get('nombre')
        agente.email = request.POST.get('email')
        agente.empresa = request.POST.get('empresa')
        agente.save()
        messages.success(request, "Agente externo actualizado correctamente.")
        return redirect('lista_usuarios')

    return render(request, 'usuarios/editar_agente_externo.html', {'agente': agente})


@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['rrhh', 'administrador'])
def eliminar_agente_externo(request, id):
    agente = get_object_or_404(AgenteExterno, id=id)

    if request.method == 'POST':
        agente.delete()
        messages.success(request, "Agente externo eliminado correctamente.")
        return redirect('lista_usuarios')

    return render(request, 'usuarios/eliminar_agente_externo.html', {'agente': agente})

# Inicio
@login_required
def inicio(request):
    empleado = Empleado.objects.get(usuario=request.user)
    accesos = []
    usuario = request.user

    # Calidad
    if es_calidad(empleado):
        accesos.append(('Ver tareas', 'lista_ordenes_trabajo'))

    # PPC
    if empleado.perfil == 'ppc':
        accesos.append(('Ver ordenes', 'lista_ordenes_trabajo'))

    # RRHH
    if es_rrhh(empleado):
        accesos.append(('Registrar usuario', 'registrar_usuario'))
        accesos.append(('Registrar agente externo', 'gestionar_externos'))
        accesos.append(('Ver ordenes', 'lista_ordenes_trabajo'))
        accesos.append(('Registrar Personal de Taller', 'personal_de_taller'))
        accesos.append(('Lista de personal', 'lista_usuarios'))

    # Administrador
    if es_admin(empleado):
        accesos.append(('Registrar usuario', 'registrar_usuario'))
        accesos.append(('Registrar agente externo', 'gestionar_externos'))
        accesos.append(('Crear orden de trabajo', 'crear_orden_trabajo'))
        accesos.append(('Ver ordenes', 'lista_ordenes_trabajo'))
        accesos.append(('Registrar Personal de Taller', 'personal_de_taller'))
        accesos.append(('Lista de personal', 'lista_usuarios'))
        #accesos.append(('admin:index', 'admin:index'))

    # Despacho
    if empleado.perfil == 'despacho':
        accesos.append(('Ver ordenes', 'lista_ordenes_trabajo'))

    # Ingeniería
    if empleado.perfil == 'ingenieria':
        accesos.append(('Ver ordenes', 'lista_ordenes_trabajo'))
        accesos.append(('Crear orden de trabajo', 'crear_orden_trabajo'))

    # Producción (Jefe)
    if empleado.perfil == 'produccion':
        accesos.append(('Ver ordenes', 'lista_ordenes_trabajo'))

    return render(request, 'inicio.html', {
        'empleado': empleado,
        'accesos': accesos
    })
#Registrar Usuarios

@login_required
def registrar_usuario(request):
    empleado = Empleado.objects.get(usuario=request.user)

    if empleado.perfil not in ['rrhh', 'administrador']:
        return HttpResponseForbidden("No tenés permiso para acceder a esta sección.")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        perfil = request.POST.get('perfil')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')

        if username and password and perfil and nombre and apellido:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=nombre,
                last_name=apellido,
            )
            Empleado.objects.create(
                usuario=user,
                perfil=perfil,
                nombre=f"{nombre} {apellido}"
            )
            messages.success(request, "Usuario creado correctamente.")
            return redirect('registrar_usuario')
        else:
            messages.error(request, "Todos los campos son obligatorios.")

    return render(request, 'rr_hh/registrar_usuario.html')


@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['rrhh', 'administrador'])
def personal_de_taller(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        perfil = request.POST.get('perfil')

        if not nombre or not apellido or perfil not in ['armador', 'soldador']:
            messages.error(request, "Completa correctamente los datos.")
            return redirect('personal_de_taller')

        Empleado.objects.create(
            usuario=None,
            perfil=perfil,
            nombre=f"{nombre} {apellido}"
        )
        messages.success(request, f"{perfil.capitalize()} registrado correctamente.")
        return redirect('personal_de_taller')

    return render(request, 'rr_hh/personal_de_taller.html')


# Añadir externos
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['rrhh', 'administrador'])
def gestionar_externos(request):
    if request.method == 'POST':
        form = AgenteExternoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestionar_externos')
    else:
        form = AgenteExternoForm()
        agentes = AgenteExterno.objects.all()
        return render(request, 'rr_hh/gestionar_externos.html', {'form': form, 'agentes': agentes})
        form = AgenteExternoForm()
        externos = Empleado.objects.filter(es_externo=True)
    return render(request, 'rr_hh/gestionar_externos.html', {'form': form, 'externos': externos})

@login_required
@user_passes_test(lambda u: hasattr(u, 'empleado') and u.empleado.perfil in ['administrador', 'produccion'])
def asignar_a_agente_externo(request):
    if request.method == 'POST':
        form = AsignarAgenteExternoForm(request.POST)
        if form.is_valid():
            tarea_id = form.cleaned_data['tarea_id']
            agente = form.cleaned_data['agente_externo']
            tarea = get_object_or_404(Tarea, id=tarea_id)
            tarea.agente_externo = agente
            tarea.asignado_a = None  # asegurarse de que no quede asignado a un interno
            tarea.save()
            messages.success(request, f"Tarea {tarea.id} asignada a {agente.nombre}.")
            return redirect('detalle_orden_trabajo', orden_id=tarea.orden.id)
    return HttpResponseBadRequest("Datos inválidos.")

@login_required
def detalle_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    empleado = Empleado.objects.get(usuario=request.user)
    porcentaje, sector_legible = calcular_progreso_por_sector(tarea.sector, tarea.estado)
    es_calidad = empleado.perfil == 'calidad'
    es_jefe_produccion = empleado.perfil == 'produccion'
    puede_ver = empleado.perfil in ['administrador', 'produccion', 'ppc', 'ingenieria', 'calidad', 'despacho']
    puede_comentar = empleado.perfil in ['ingenieria', 'produccion', 'calidad', 'administrador']

    if not puede_ver:
        return HttpResponseForbidden("No tenés permiso para ver esta tarea.")

    if request.method == 'POST':
        accion = request.POST.get('accion')
        destino_final = request.POST.get('destino_final')  # puede ser None

        # Reasignación
        if accion == 'reasignar' and puede_asignar(empleado):
            tipo = request.POST.get('tipo_asignacion')
            if tipo == 'tercerizado':
                agente_id = request.POST.get('agente_externo_id')
                if agente_id:
                    agente = get_object_or_404(AgenteExterno, id=agente_id)
                    tarea.agente_externo = agente
                    tarea.asignado_a = None
                    tarea.save()
            elif tipo == 'empleado':
                operario_id = request.POST.get('asignado_id')
                if operario_id and operario_id != 'tercerizado':
                    operario = get_object_or_404(
                        Empleado,
                        id=operario_id,
                        perfil__in=['armador', 'soldador'],
                    )
                    tarea.asignado_a = operario
                    tarea.agente_externo = None
                    tarea.save()
            messages.success(request, "Tarea reasignada correctamente.")
            return redirect('detalle_tarea', tarea.id)
        
        if accion == 'cambiar_sector' and es_jefe_produccion:
            nuevo_sector = request.POST.get('nuevo_sector')

            if nuevo_sector:
                tarea.sector = nuevo_sector

            # Actualizar el estado automáticamente según el sector
                if nuevo_sector in ['armado', 'soldado']:
                    tarea.estado = 'en_progreso'
                elif nuevo_sector in ['control_1', 'control_2']:
                    tarea.estado = 'en_revision'
                elif nuevo_sector == 'pintado':
                    tarea.estado = 'lista_para_pintar'
                elif nuevo_sector == 'despachar':
                    tarea.estado = 'lista_para_despachar'
                elif nuevo_sector == 'galvanizado':
                    tarea.estado = 'galvanizado'
                elif nuevo_sector == 'pendiente':
                    tarea.estado = 'pendiente'

            tarea.save()
            messages.success(request, 'El sector y estado fueron actualizados correctamente.')
            return redirect('detalle_tarea', tarea.id)

        # Comentario
        if accion == 'agregar_comentario' and puede_comentar:
            form = ComentarioForm(request.POST, request.FILES)
            if form.is_valid():
                comentario = form.save(commit=False)
                comentario.tarea = tarea
                comentario.autor = empleado
                comentario.save()
                messages.success(request, "Comentario agregado.")
                return redirect('detalle_tarea', tarea.id)

        # Producción: enviar a control de calidad
        if accion == 'enviar_revision' and es_jefe_produccion:
            tarea.estado = 'en_revision'
            tarea.sector = 'control'
            tarea.save()
            messages.success(request, "Tarea enviada a control de calidad.")
            return redirect('detalle_orden_trabajo', tarea.orden.id)

        # Calidad: aceptar o rechazar
        if es_calidad and accion == 'aceptar':
            if tarea.sector == 'control_1':
                tarea.estado = 'pendiente'
                tarea.sector = 'soldado'
                tarea.save()
                messages.success(request, "Tarea aprobada. Ahora debe ser asignada a soldador.")
                return redirect('detalle_tarea', tarea.id)
            elif tarea.sector == 'control_2':
                messages.success(request, "Tarea aprobada. Producción debe elegir destino final.")
                return redirect('detalle_tarea', tarea.id)
            else:
                messages.warning(request, "No se reconoce esta etapa para validación.")
        elif accion == 'rechazar':
                tarea.estado = 'rechazada'
                tarea.save()
                messages.success(request, "Tarea rechazada.")
                return redirect('detalle_orden_trabajo', tarea.orden.id)
        
        if accion == 'enviar_a_despacho' and es_calidad:
            tarea.estado = 'lista_para_despachar'
            tarea.sector = 'despachar'
            tarea.save()
            messages.success(request, "La tarea fue enviada al sector Despacho.")
            return redirect('detalle_tarea', tarea.id)

        avanzar_tarea(tarea, accion, empleado, destino_final)
        messages.success(request, "La tarea fue actualizada.")
        return redirect('detalle_tarea', tarea.id)

    context = {
        'tarea': tarea,
        'es_calidad': es_calidad,
        'es_jefe_produccion': es_jefe_produccion,
        'comentarios': tarea.comentarios.select_related('autor').order_by('fecha_creacion'),
        'comentario_form': ComentarioForm(),
        'puede_comentar': puede_comentar,
        'perfil_usuario': empleado.perfil,
        'porcentaje': porcentaje,
        'sector_legible': sector_legible,
    }

    if puede_asignar(empleado):
        context.update({
            'operarios': Empleado.objects.filter(perfil__in=['armador', 'soldador']),
            'agentes_externos': AgenteExterno.objects.filter(activo=True),
            'puede_asignar': True,
        })

    return render(request, 'tareas/detalle_tarea.html', context)


@user_passes_test(es_admin_o_ingenieria)
def editar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    if request.method == "POST":
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarea modificada correctamente.")
            return redirect('detalle_tarea', tarea_id=tarea.id)
    else:
        form = TareaForm(instance=tarea)
    del form.fields['orden']
    es_ingenieria = request.user.empleado.perfil == 'ingenieria'
    if es_ingenieria:
        del form.fields['estado']
        del form.fields['sector']
        del form.fields['asignado_a']
        del form.fields['agente_externo']

        
    
    return render(request, 'tareas/editar_tarea.html', {'form': form, 'tarea': tarea})

@login_required
def crear_orden_trabajo(request):
    empleado = Empleado.objects.get(usuario=request.user)

    if not puede_asignar(empleado):
        return HttpResponseForbidden("No tenés permiso para crear órdenes.")

    if request.method == 'POST':
        form = OrdenDeTrabajoForm(request.POST, request.FILES)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.creada_por = empleado
            orden.save()

            if orden.archivo_excel:
                procesar_excel_y_crear_tareas(orden.archivo_excel, orden, empleado)

            return redirect('lista_ordenes_trabajo')
    else:
        form = OrdenDeTrabajoForm()

    return render(request, 'tareas/crear_orden_trabajo.html', {'form': form})

def lista_ordenes_trabajo(request):
    empleado = Empleado.objects.get(usuario=request.user)

    if not puede_ver_avances(empleado):
        return HttpResponseForbidden("No tenés permiso para ver las órdenes de trabajo.")

    # 🔎 Filtrado de órdenes según perfil
    if empleado.perfil == 'calidad':
        ordenes = OrdenDeTrabajo.objects.filter(tareas__estado='en_revision').distinct()
    elif empleado.perfil == 'despacho':
        ordenes = OrdenDeTrabajo.objects.filter(tareas__estado='lista_para_despachar').distinct()
    else:
        ordenes = OrdenDeTrabajo.objects.all()

    SECTORES_PROGRESO = [
        'armado', 'control_1', 'soldado', 'control_2',
        'pintado', 'galvanizado', 'despachar'
    ]

    def calcular_progreso_por_sector(sector_actual, estado_actual=None):
        if estado_actual == 'finalizada':
            return 100
        try:
            indice = SECTORES_PROGRESO.index(sector_actual)
            return int((indice + 1) / len(SECTORES_PROGRESO) * 100)
        except ValueError:
            return 0

    ordenes_con_info = []
    for orden in ordenes:
        tareas = Tarea.objects.filter(orden=orden)
        total = tareas.count()
        completadas = tareas.filter(estado='finalizada').count()

        if total > 0:
            progreso = sum([calcular_progreso_por_sector(t.sector, t.estado) for t in tareas]) // total
        else:
            progreso = 0

        # ✅ Solo actualiza si es necesario
        if progreso == 100:
            if not orden.finalizada:
                orden.finalizada = True
                orden.save()
        else:
            if orden.finalizada:
                orden.finalizada = False
                orden.save()
            ordenes_con_info.append({
                'orden': orden,
                'total': total,
                'completadas': completadas,
                'progreso': progreso
            })

    return render(request, 'tareas/lista_ordenes_trabajo.html', {
        'ordenes': ordenes_con_info,
        'perfil_usuario': empleado.perfil
    })

@login_required
def detalle_orden_trabajo(request, orden_id):
    orden = get_object_or_404(OrdenDeTrabajo, id=orden_id)
    empleado = Empleado.objects.get(usuario=request.user)
    tipo = None
    

    if not puede_ver_avances(empleado):
        return HttpResponseForbidden("No tenés acceso a esta orden.")

    if request.method == 'POST' and puede_asignar(empleado):
        tarea_id = request.POST.get('tarea_id')
        tipo = request.POST.get('tipo_asignacion')
        tarea = get_object_or_404(orden.tareas, id=tarea_id)

    if tipo == 'tercerizado':
        agente_id = request.POST.get('agente_externo_id')
        if agente_id:
            agente = get_object_or_404(AgenteExterno, id=agente_id)
            tarea.agente_externo = agente
            tarea.asignado_a = None
            tarea.save()

    elif tipo == 'empleado':
        operario_id = request.POST.get('asignado_id')
        if operario_id and operario_id != 'tercerizado':
            operario = get_object_or_404(
                Empleado,
                id=operario_id,
                perfil__in=['armador', 'soldador',]
            )
            tarea.asignado_a = operario
            tarea.agente_externo = None
            tarea.save()
        return redirect('detalle_orden_trabajo', orden_id=orden.id)

    tareas = orden.tareas.all()
    if empleado.perfil == 'calidad':
        tareas = tareas.filter(estado='en_revision')

    if empleado.perfil == 'despacho':
        tareas = tareas.filter(estado='lista_para_despachar')

    busqueda = request.GET.get('q', '')
    if busqueda:
        tareas = tareas.filter(titulo__icontains=busqueda)

    estado = request.GET.get('estado', '')
    if estado:
        tareas = tareas.filter(estado=estado)

    paginator = Paginator(tareas, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    operarios = Empleado.objects.filter(perfil__in=['armador', 'soldador',])
    agentes_externos = AgenteExterno.objects.filter(activo=True)

    es_admin = empleado.perfil == 'administrador'
    es_produccion = empleado.perfil == 'produccion'
    puede_asignar_valor = es_admin or es_produccion

    return render(request, 'tareas/detalle_orden_trabajo.html', {
        'orden': orden,
        'tareas': page_obj,
        'operarios': operarios,
        'perfil_usuario': empleado.perfil,
        'busqueda': busqueda,
        'estado_seleccionado': estado,
        'puede_asignar': puede_asignar_valor,
        'agentes_externos': agentes_externos,
    })

@login_required
def borrar_orden_trabajo(request, orden_id):
    empleado = Empleado.objects.get(usuario=request.user)

    if not puede_asignar(empleado):
        return HttpResponseForbidden("No tenés permiso para borrar órdenes de trabajo.")
    orden = get_object_or_404(OrdenDeTrabajo, id=orden_id)

    if request.method == 'POST':
        orden.delete()
        messages.success(request, f"La Orden de Trabajo {orden.nombre} fue eliminada.")
        return redirect('lista_ordenes_trabajo')

    return render(request, 'tareas/confirmar_borrado_ot.html', {'orden': orden})

@login_required
def historial_ordenes_trabajo(request):
    todas_las_ots = OrdenDeTrabajo.objects.all()
    
    ordenes_finalizadas = []
    for ot in todas_las_ots:
        tareas = ot.tareas.all()
        total = tareas.count()
        completadas = tareas.filter(estado='finalizada').count()
        
        if total > 0 and total == completadas:
            ordenes_finalizadas.append({
                'orden': ot,
                'total': total,
                'completadas': completadas,
            })

    return render(request, 'tareas/historial_ordenes.html', {'ordenes': ordenes_finalizadas})
# Crear y eliminar tareas
@login_required
def crear_tarea(request, orden_id):
    empleado = Empleado.objects.get(usuario=request.user)
    if empleado.perfil not in ['ingenieria', 'administrador']:
        return HttpResponseForbidden("No tenés permiso para crear tareas.")

    orden = get_object_or_404(OrdenDeTrabajo, id=orden_id)

    if request.method == 'POST':
        form = TareaForm(request.POST)

        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.orden = orden
            tarea.creada_por = empleado
            tarea.save()
            messages.success(request, "Tarea creada correctamente.")
            return redirect('detalle_orden_trabajo', orden_id=orden.id)
    else:
        form = TareaForm()

    return render(request, 'tareas/crear_tarea.html', {'form': form, 'orden': orden})


@login_required
def borrar_tarea(request, tarea_id):
    empleado = Empleado.objects.get(usuario=request.user)
    if empleado.perfil not in ['ingenieria', 'administrador']:
        return HttpResponseForbidden("No tenés permiso para borrar tareas.")

    tarea = get_object_or_404(Tarea, id=tarea_id)
    if request.method == 'POST':
        orden_id = tarea.orden.id
        tarea.delete()
        messages.success(request, "Tarea eliminada correctamente.")
        return redirect('detalle_orden_trabajo', orden_id=orden_id)

    return render(request, 'tareas/confirmar_borrado_tarea.html', {'tarea': tarea})

# Procesar Excel
def procesar_excel_y_crear_tareas(archivo_excel, orden, creador):

    df = pd.read_excel(archivo_excel, sheet_name='GRAL', skiprows=6)
    df.columns = df.columns.str.strip()

    print("✅ Columnas detectadas:", df.columns.tolist())

    columnas_esperadas = [
        'POSICIÓN', 'ID. ESTRUCT.', 'PLANO CMMT', 'DENOMINACIÓN', 'CANTIDAD',
        'PESO UNIT.', 'PESO TOTAL'
    ]

    for col in columnas_esperadas:
        if col not in df.columns:
            raise ValueError(f"❌ Falta la columna requerida: {col}")
        

    for _, row in df.iterrows():


        # Limpieza numérica segura
        def limpiar_numero(valor):
            if pd.isna(valor):
                return None
            try:
                return int(valor)
            except:
                try:
                    return float(valor)
                except:
                    return None

        cantidad = limpiar_numero(row['CANTIDAD'])
        peso_unit = limpiar_numero(row['PESO UNIT.'])
        peso_total = limpiar_numero(row['PESO TOTAL'])

        # Campos clave para validar existencia de la tarea
        plano = row['PLANO CMMT']
        denominacion = row['DENOMINACIÓN']
        estructura = row['ID. ESTRUCT.']
        
        if pd.isna(plano) or plano == "":
            print("⚠️Fila ignorada por plano vacío.")
            continue

        Tarea.objects.create(
            titulo=f"{plano} - {denominacion}",
            descripcion=f"Posición: {row['POSICIÓN']}, Estructura: {estructura}",
            asignado_a=None,
            creada_por=creador,
            orden=orden,
            estado='pendiente',

            estructura=estructura,
            plano_codigo=plano,
            posicion=row['POSICIÓN'],
            denominacion=denominacion,
            cantidad=cantidad,
            peso_unitario=peso_unit,
            peso_total=peso_total,
        )

def procesar_excel_y_actualizar_tareas(archivo_excel, orden, creador):
    import pandas as pd
    from .models import Tarea

    df = pd.read_excel(archivo_excel, sheet_name='GRAL', skiprows=6)
    df.columns = df.columns.str.strip()

    print("✅ Columnas detectadas:", df.columns.tolist())

    columnas_esperadas = [
        'POSICIÓN', 'ID. ESTRUCT.', 'PLANO CMMT', 'DENOMINACIÓN', 'CANTIDAD',
        'PESO UNIT.', 'PESO TOTAL'
    ]

    for col in columnas_esperadas:
        if col not in df.columns:
            raise ValueError(f"❌ Falta la columna requerida: {col}")

    # Función de limpieza numérica
    def limpiar_numero(valor):
        if pd.isna(valor):
            return None
        try:
            return int(valor)
        except:
            try:
                return float(valor)
            except:
                return None

    actualizadas = 0
    creadas = 0

    for _, row in df.iterrows():
        plano = row['PLANO CMMT']
        denominacion = row['DENOMINACIÓN']
        estructura = row['ID. ESTRUCT.']
        posicion = row['POSICIÓN']

        if pd.isna(plano) or plano == "":
            print("⚠️ Fila ignorada por plano vacío.")
            continue

        cantidad = limpiar_numero(row['CANTIDAD'])
        peso_unit = limpiar_numero(row['PESO UNIT.'])
        peso_total = limpiar_numero(row['PESO TOTAL'])

        # Identificador único para buscar si ya existe
        titulo = f"{plano} - {denominacion}"

        tarea_existente = Tarea.objects.filter(titulo=titulo, orden=orden).first()

        if tarea_existente:
            tarea_existente.descripcion = f"Posición: {posicion}, Estructura: {estructura}"
            tarea_existente.estructura = estructura
            tarea_existente.plano_codigo = plano
            tarea_existente.posicion = posicion
            tarea_existente.denominacion = denominacion
            tarea_existente.cantidad = cantidad
            tarea_existente.peso_unitario = peso_unit
            tarea_existente.peso_total = peso_total
            tarea_existente.save()
            actualizadas += 1
        else:
            Tarea.objects.create(
                titulo=titulo,
                descripcion=f"Posición: {posicion}, Estructura: {estructura}",
                asignado_a=None,
                creada_por=creador,
                orden=orden,
                estado='pendiente',
                estructura=estructura,
                plano_codigo=plano,
                posicion=posicion,
                denominacion=denominacion,
                cantidad=cantidad,
                peso_unitario=peso_unit,
                peso_total=peso_total,
            )
            creadas += 1

    return f"Tareas actualizadas: {actualizadas}, nuevas creadas: {creadas}"

@login_required
def importar_excel_actualizacion(request, orden_id):
    orden = get_object_or_404(OrdenDeTrabajo, id=orden_id)
    empleado = Empleado.objects.get(usuario=request.user)

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo_excel = request.FILES['archivo_excel']

        mensaje = procesar_excel_y_actualizar_tareas(archivo_excel, orden, empleado)
        messages.success(request, mensaje)
        return redirect('detalle_orden_trabajo', orden_id=orden.id)

    return render(request, 'tareas/importar_excel_actualizacion.html', {'orden': orden})

# Estados en orden lógico
SECTORES_PROGRESO = [
    'armado',
    'control_1',
    'soldado',
    'control_2',
    'pintado',
    'galvanizado',
    'despachar',
    'finalizado'
]

def calcular_progreso_por_sector(sector_actual, estado_actual=None):
    if estado_actual == 'finalizada':
        return 100, 'Finalizada'
    try:
        indice = SECTORES_PROGRESO.index(sector_actual)
        porcentaje = int((indice + 1) / len(SECTORES_PROGRESO) * 100)
        sector_legible = sector_actual.replace("_", " ").capitalize()
        return porcentaje, sector_legible
    except ValueError:
        return 0, "Sin sector"

# Cerrar sesion
def cerrar_sesion(request):
    if request.method == 'GET':
        logout(request)
        return redirect('login')
    return redirect('home')  # opcional: manejar otros métodos



