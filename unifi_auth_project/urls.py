"""
URL configuration for unifi_auth_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from unifi_auth_app import views
from django.contrib.auth.decorators import user_passes_test
from django_prometheus import exports

# Apenas superusuários podem acessar as métricas
is_superuser = user_passes_test(lambda u: u.is_superuser)

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin do Django
    path('login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('api/authorize/', views.authorize_guest_api, name='authorize_guest_api'),  # API de autorização
    path('', include('unifi_auth_app.urls')),
    # Endpoint de métricas protegido por autenticação
    path('metrics/', is_superuser(exports.ExportToDjangoView), name='django-prometheus-metrics'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
