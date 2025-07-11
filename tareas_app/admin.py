from django.contrib import admin
from .models import Empleado, Tarea, Comentario

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'perfil']
    search_fields = ['usuario__username', 'perfil']

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'asignado_a', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'asignado_a']
    search_fields = ['titulo', 'descripcion']
    list_editable = ['estado']
    readonly_fields = ['fecha_creacion']
    fieldsets = (
        (None, {
            'fields': ('titulo', 'descripcion')
        }),
        ('Asignación', {
            'fields': ('asignado_a', 'creada_por')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_creacion')
        }),
    )


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ["tarea", "autor", "fecha_creacion"]
    search_fields = ["texto", "autor__nombre"]
