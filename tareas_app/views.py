from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Tarea, Empleado, OrdenDeTrabajo
from django.contrib.auth.models import User
from .forms import TareaForm, OrdenDeTrabajoForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages
import pandas as pd
import numpy as np

def es_admin(empleado):
    return empleado.perfil == 'administrador'

def puede_asignar(empleado):
    return empleado.perfil in ['administrador', 'produccion']

def puede_ver_avances(empleado):
    return empleado.perfil in ['administrador', 'ppc', 'produccion', 'calidad', 'despacho', 'ingenieria', 'rrhh']

def es_calidad(empleado):
    return empleado.perfil == 'calidad'

def es_operario(empleado):
    return empleado.perfil in ['armador', 'soldador', 'pintor', 'corte']


@login_required
def redirect_por_perfil(request):
    return redirect('lista_ordenes_trabajo')


#Registrar Usuarios

@login_required
def registrar_usuario(request):
    empleado = Empleado.objects.get(usuario=request.user)

    if empleado.perfil != 'rrhh':
        return HttpResponseForbidden("No tenés permiso para acceder a esta sección.")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        perfil = request.POST.get('perfil')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')

        if username and password and perfil and nombre and apellido:
            user = User.objects.create_user(username=username, password=password, first_name=nombre, last_name=apellido)
            Empleado.objects.create(usuario=user, perfil=perfil)
            messages.success(request, "Usuario creado correctamente.")
            return redirect('registrar_usuario')
        else:
            messages.error(request, "Todos los campos son obligatorios.")

    return render(request, 'rr_hh/registrar_usuario.html')


@login_required
def detalle_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    empleado = Empleado.objects.get(usuario=request.user)

    es_calidad = empleado.perfil == 'calidad'
    puede_ver = empleado.perfil in ['administrador', 'produccion', 'ppc', 'ingenieria', 'calidad', 'despacho']

    if not puede_ver:
        return HttpResponseForbidden("No tenés permiso para ver esta tarea.")

    if request.method == 'POST' and es_calidad:
        accion = request.POST.get('accion')

        if accion == 'aceptar':
            tarea.estado = 'finalizada'
            tarea.save()
            messages.success(request, "Tarea aceptada correctamente.")
            return redirect('detalle_orden_trabajo', tarea.orden.id)

        elif accion == 'rechazar':
            tarea.estado = 'rechazada'
            tarea.save()
            messages.success(request, "Tarea rechazada.")
            return redirect('detalle_orden_trabajo', tarea.orden.id)

    return render(request, 'tareas/detalle_tarea.html', {
        'tarea': tarea,
        'es_calidad': es_calidad
    })


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

@login_required
def lista_ordenes_trabajo(request):
    empleado = Empleado.objects.get(usuario=request.user)

    if not puede_ver_avances(empleado):
        return HttpResponseForbidden("No tenés permiso para ver las órdenes de trabajo.")

    if empleado.perfil == 'calidad':
        ordenes = OrdenDeTrabajo.objects.filter(tareas__estado='en_revision').distinct()
    else:
        ordenes = OrdenDeTrabajo.objects.all()

    ordenes_con_info = []
    for orden in ordenes:
        total = orden.tareas.count()
        completadas = orden.tareas.filter(estado='finalizada').count()
        progreso = int((completadas / total) * 100) if total > 0 else 0

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

    if not puede_ver_avances(empleado):
        return HttpResponseForbidden("No tenés acceso a esta orden.")

    if request.method == 'POST' and puede_asignar(empleado):
        tarea_id = request.POST.get('tarea_id')
        operario_id = request.POST.get('operario_id')

        tarea = get_object_or_404(orden.tareas, id=tarea_id)
        operario = get_object_or_404(Empleado, id=operario_id, perfil__in=['armador', 'soldador', 'pintor', 'corte'])

        tarea.asignado_a = operario
        tarea.save()
        messages.success(request, f"Tarea {tarea.id} asignada a {operario.nombre}.")
        return redirect('detalle_orden_trabajo', orden_id=orden.id)

    tareas = orden.tareas.all()

    busqueda = request.GET.get('q', '')
    if busqueda:
        tareas = tareas.filter(titulo__icontains=busqueda)

    estado = request.GET.get('estado', '')
    if estado:
        tareas = tareas.filter(estado=estado)

    paginator = Paginator(tareas, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    operarios = Empleado.objects.filter(perfil__in=['armador', 'soldador', 'pintor', 'corte'])

    es_admin = empleado.perfil == 'administrador'
    es_produccion = empleado.perfil == 'produccion'
    puede_asignar = es_admin or es_produccion

    return render(request, 'tareas/detalle_orden_trabajo.html', {
    'orden': orden,
    'tareas': page_obj,
    'operarios': operarios,
    'perfil_usuario': empleado.perfil,
    'busqueda': busqueda,
    'estado_seleccionado': estado,
    'puede_asignar': puede_asignar
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
        
        if pd.isna(estructura) or pd.isna(denominacion):
            print("⚠️ Fila ignorada por falta de datos esenciales.")
            continue  # Salta esta fila

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

# Cerrar sesion
def cerrar_sesion(request):
    if request.method == 'GET':
        logout(request)
        return redirect('login')
    return redirect('home')  # opcional: manejar otros métodos



