from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_tareas, name='lista_tareas'),  # /tareas/
    path('<int:tarea_id>/', views.detalle_tarea, name='detalle_tarea'),
    path('crear/', views.crear_tarea, name='crear_tarea'),
    path('operario/', views.tareas_operario, name='tareas_operario'),
    path('operario/<int:tarea_id>/completar/', views.marcar_completada, name='marcar_completada'),
    path('operario/<int:tarea_id>/', views.detalle_tarea_operario, name='detalle_tarea_operario'),
    path('controlador/', views.tareas_para_controlar, name='tareas_para_controlar'),
    path('controlador/<int:tarea_id>/resolver/', views.resolver_tarea, name='resolver_tarea'),
    path('controlador/<int:tarea_id>/', views.detalle_tarea_controlador, name='detalle_tarea_controlador'),
    path('ordenes/', views.lista_ordenes_trabajo, name='lista_ordenes_trabajo'),
    path('ordenes/crear/', views.crear_orden_trabajo, name='crear_orden_trabajo'),
    path('ordenes/<int:orden_id>/', views.detalle_orden_trabajo, name='detalle_orden_trabajo'),
    path('orden_trabajo/<int:orden_id>/eliminar/', views.eliminar_orden_trabajo, name='eliminar_orden_trabajo'),
]
