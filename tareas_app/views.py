from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Tarea, Empleado
from django.contrib.auth.models import User
from .forms import TareaForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout

@login_required
def redirect_por_perfil(request):
    perfil = request.user.empleado.perfil
    if perfil == 'encargado':
        return redirect('lista_tareas')
    elif perfil == 'operario':
        return redirect('tareas_operario')
    elif perfil == 'controlador':
        return redirect('tareas_para_controlar')
    else:
        return redirect('login')

@login_required
def lista_tareas(request):
    empleado = get_object_or_404(Empleado, usuario=request.user)
    if empleado.perfil == 'operario':
        tareas = Tarea.objects.filter(asignado_a=empleado)
    elif empleado.perfil == 'controlador':
        tareas = Tarea.objects.filter(estado='en_progreso')
    else:
        tareas = Tarea.objects.all()
    return render(request, 'tareas/lista_tareas.html', {'tareas': tareas})

@login_required
def detalle_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    empleado = Empleado.objects.get(usuario=request.user)

    es_operario = empleado.perfil == 'operario'
    es_controlador = empleado.perfil == 'controlador'
    es_encargado = empleado.perfil == 'encargado'

    # Validación de acceso por perfil
    #if es_operario and tarea.asignado_a != empleado:
        #return HttpResponseForbidden("No tenés permiso para ver esta tarea.")
    if es_operario:
        if tarea.asignado_a != empleado:
            return HttpResponseForbidden("No tenés permiso para ver esta tarea.")

    elif es_controlador:
        if tarea.estado not in ['en_revision', 'finalizada', 'rechazada']:
            return HttpResponseForbidden("Solo podés acceder a tareas en revisión o ya resueltas.")
        
    elif not es_encargado:
        # Solo prohíbe si no es ninguno de los perfiles aceptados
        return HttpResponseForbidden("No tenés permiso para ver esta tarea.")    


    if request.method == 'POST':
        accion = request.POST.get('accion')

        if es_operario and accion == 'enviar_control':
            tarea.estado = 'en_revision'
            tarea.save()

        elif es_controlador:
            if accion == 'aceptar':
                tarea.estado = 'finalizada'
            elif accion == 'rechazar':
                tarea.estado = 'pendiente'
                tarea.save()
                tarea.generar_pdf()
            elif accion == 'rechazada':
                tarea.estado = 'rechazada'
            tarea.save()

    return render(request, 'tareas/detalle_tarea.html', {
        'tarea': tarea,
        'es_operario': es_operario,
        'es_controlador': es_controlador,
        'es_encargado': es_encargado,
    })


@login_required
def crear_tarea(request):
    empleado = Empleado.objects.get(usuario=request.user)

    if empleado.perfil != 'encargado':
        return HttpResponseForbidden("Solo los encargados pueden crear tareas.")

    if request.method == 'POST':
        form = TareaForm(request.POST, request.FILES)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.creada_por = empleado
            tarea.estado = 'pendiente'
            tarea.save()
            return redirect('lista_tareas')  # Redirige a la lista después de crear
    else:
        form = TareaForm()

    return render(request, 'tareas/crear_tarea.html', {'form': form})


@login_required
def tareas_operario(request):
    empleado = Empleado.objects.get(usuario=request.user)
    if empleado.perfil != 'operario':
        return HttpResponseForbidden("Solo operarios pueden ver esta página.")

    tareas = Tarea.objects.filter(asignado_a=empleado)
    return render(request, 'tareas/tareas_operario.html', {'tareas': tareas})

@require_POST
@login_required
def marcar_completada(request, tarea_id):
    empleado = Empleado.objects.get(usuario=request.user)
    tarea = Tarea.objects.get(id=tarea_id)

    if tarea.asignado_a != empleado or empleado.perfil != 'operario':
        return HttpResponseForbidden("No podés modificar esta tarea.")

    tarea.estado = 'en_revision'
    tarea.save()
    return HttpResponseRedirect(reverse('tareas_operario'))

@login_required
def tareas_para_controlar(request):
    empleado = Empleado.objects.get(usuario=request.user)
    if empleado.perfil != 'controlador':
        return HttpResponseForbidden("Solo controladores pueden ver esta página.")

    tareas = Tarea.objects.filter(estado='en_revision')
    return render(request, 'tareas/tareas_controlador.html', {'tareas': tareas})

@require_POST
@login_required
def resolver_tarea(request, tarea_id):
    empleado = Empleado.objects.get(usuario=request.user)
    if empleado.perfil != 'controlador':
        return HttpResponseForbidden("No autorizado.")

    tarea = Tarea.objects.get(id=tarea_id)
    accion = request.POST.get('accion')

    if accion == 'aceptar':
        tarea.estado = 'finalizada'
    elif accion == 'rechazar':
        tarea.estado = 'pendiente'
    tarea.save()

    return HttpResponseRedirect(reverse('tareas_para_controlar'))


def cerrar_sesion(request):
    if request.method == 'GET':
        logout(request)
        return redirect('login')
    return redirect('home')  # opcional: manejar otros métodos

def detalle_tarea_operario(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    return render(request, 'detalle_tarea_operario.html', {'tarea': tarea})

def detalle_tarea_controlador(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    return render(request, 'detalle_tarea_controlador.html', {'tarea': tarea})



# Create your views here.
