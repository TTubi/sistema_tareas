from django.urls import path
from . import views
from .views import lista_usuarios_completa, CustomLoginView


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('<int:tarea_id>/', views.detalle_tarea, name='detalle_tarea'),
    path('ordenes/', views.lista_ordenes_trabajo, name='lista_ordenes_trabajo'),
    path('ordenes/crear/', views.crear_orden_trabajo, name='crear_orden_trabajo'),
    path('ordenes/<int:orden_id>/', views.detalle_orden_trabajo, name='detalle_orden_trabajo'),
    path('ordenes/<int:orden_id>/tareas/nueva/', views.crear_tarea, name='crear_tarea'),
    path('tareas/<int:tarea_id>/borrar/', views.borrar_tarea, name='borrar_tarea'),
    path('ordenes/<int:orden_id>/borrar/', views.borrar_orden_trabajo, name='borrar_orden_trabajo'),
    path('registrar-usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('rrhh/externos/', views.gestionar_externos, name='gestionar_externos'),
    path('asignar_agente_externo/', views.asignar_a_agente_externo, name='asignar_a_agente_externo'),
    path('inicio/', views.inicio, name='inicio'),
    path('personal-de-taller/', views.personal_de_taller, name='personal_de_taller'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/', views.lista_usuarios_completa, name='lista_usuarios'),
    path('personal-taller/<int:id>/editar/', views.editar_personal_taller, name='editar_personal_taller'),
    path('personal-taller/<int:id>/eliminar/', views.eliminar_personal_taller, name='eliminar_personal_taller'),
    path('rrhh/externos/', views.gestionar_externos, name='externos'),
    path('externos/<int:id>/editar/', views.editar_agente_externo, name='editar_agente_externo'),
    path('externos/<int:id>/eliminar/', views.eliminar_agente_externo, name='eliminar_agente_externo'),
]
