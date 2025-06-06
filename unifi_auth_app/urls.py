from django.urls import path
from . import views

app_name = 'unifi_auth_app'

urlpatterns = [
    path('', views.home, name='home'),  # Página inicial
]
