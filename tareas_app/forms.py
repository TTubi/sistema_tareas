from django import forms
from .models import Tarea, Empleado, OrdenDeTrabajo

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'asignado_a', 'plano']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo empleados que sean operarios en el campo asignado_a
        self.fields['asignado_a'].queryset = Empleado.objects.filter(perfil='operario')

class OrdenDeTrabajoForm(forms.ModelForm):
    class Meta:
        model = OrdenDeTrabajo
        fields = ['nombre', 'descripcion', 'archivo_excel']

class AsignarOperarioForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['asignado_a']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asignado_a'].queryset = Empleado.objects.filter(perfil='operario')