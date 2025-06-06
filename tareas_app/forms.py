from django import forms
from .models import Tarea, Empleado

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'asignado_a', 'plano']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo empleados que sean operarios en el campo asignado_a
        self.fields['asignado_a'].queryset = Empleado.objects.filter(perfil='operario')
