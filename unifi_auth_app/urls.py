from django.urls import path
from . import views

app_name = 'unifi_auth_app'

urlpatterns = [
    # Páginas web
    path('', views.home, name='home'),
    
    # API Endpoints
    path('api/check-auth/', views.check_auth_status, name='check_auth_status'),
    path('api/authorize-visitor/', views.authorize_visitor, name='authorize_visitor'),
    
    # Endpoint antigo (mantido para compatibilidade)
    path('api/authorize-guest/', views.authorize_guest_api, name='authorize_guest_api'),
]
