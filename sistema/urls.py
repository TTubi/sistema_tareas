from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from tareas_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.redirect_por_perfil, name='home'),  # home redirige según perfil
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('tareas/', include('tareas_app.urls')),  # ✅ OK, solo en /tareas/
    path('cerrar/', views.cerrar_sesion, name='cerrar'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
