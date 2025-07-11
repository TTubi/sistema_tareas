from django import forms
from django.contrib.auth.models import User
from .models import Tarea, Empleado, OrdenDeTrabajo, AgenteExterno

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = [
            'titulo',
            'descripcion',
            'estructura',
            'plano_codigo',
            'posicion',
            'denominacion',
            'cantidad',
            'peso_unitario',
            'peso_total',
        ]

class OrdenDeTrabajoForm(forms.ModelForm):
    class Meta:
        model = OrdenDeTrabajo
        fields = ['nombre', 'descripcion', 'archivo_excel']

#class AsignarOperarioForm(forms.ModelForm):
 #   class Meta:
  #      model = Tarea
   #     fields = ['asignado_a']
class AsignarOperarioForm(forms.ModelForm):
    tipo_asignacion = forms.ChoiceField(choices=[('propio', 'Interno'), ('tercerizado', 'Externo')])
    asignado_a = forms.ModelChoiceField(queryset=Empleado.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipo = self.data.get('tipo_asignacion')
        if tipo == 'tercerizado':
            self.fields['asignado_a'].queryset = Empleado.objects.filter(es_externo=True)
        else:
            self.fields['asignado_a'].queryset = Empleado.objects.filter(perfil='operario', es_externo=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asignado_a'].queryset = Empleado.objects.filter(perfil='operario')


class AgenteExternoForm(forms.ModelForm):
    class Meta:
        model = AgenteExterno
        fields = ['nombre', 'empresa', 'contacto', 'activo']

class AsignarAgenteExternoForm(forms.Form):
    tarea_id = forms.IntegerField(widget=forms.HiddenInput())
    agente_externo = forms.ModelChoiceField(queryset=AgenteExterno.objects.filter(activo=True))
