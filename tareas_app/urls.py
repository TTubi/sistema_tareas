from django.urls import path
from . import views

urlpatterns = [
    path('<int:tarea_id>/', views.detalle_tarea, name='detalle_tarea'),
    path('ordenes/', views.lista_ordenes_trabajo, name='lista_ordenes_trabajo'),
    path('ordenes/crear/', views.crear_orden_trabajo, name='crear_orden_trabajo'),
    path('ordenes/<int:orden_id>/', views.detalle_orden_trabajo, name='detalle_orden_trabajo'),
    path('ordenes/<int:orden_id>/borrar/', views.borrar_orden_trabajo, name='borrar_orden_trabajo'),
    path('registrar-usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('rrhh/externos/', views.gestionar_externos, name='gestionar_externos'),
    path('asignar_agente_externo/', views.asignar_a_agente_externo, name='asignar_a_agente_externo'),
    path('inicio/', views.inicio, name='inicio'),
]
