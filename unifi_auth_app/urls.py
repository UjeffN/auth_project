from django.urls import path, re_path
from django.contrib.auth.decorators import permission_required
from django.conf import settings

from . import views

app_name = 'unifi_auth_app'

# Handlers de erro personalizados - definidos em settings.py
# Essas variáveis são usadas pelo Django para mapear os handlers de erro
# As definições reais estão em settings.py

# URLs para gerenciamento de dispositivos de visitantes
dispositivo_urls = [
    path(
        'dispositivos/',
        permission_required('unifi_auth_app.view_visitantedispositivo')(
            views.VisitanteDispositivoListView.as_view()
        ),
        name='visitante_dispositivo_list'
    ),
    path(
        'dispositivos/adicionar/',
        permission_required('unifi_auth_app.add_visitantedispositivo')(
            views.VisitanteDispositivoCreateView.as_view()
        ),
        name='visitante_dispositivo_create'
    ),
    path(
        'dispositivos/<int:pk>/',
        permission_required('unifi_auth_app.view_visitantedispositivo')(
            views.VisitanteDispositivoDetailView.as_view()
        ),
        name='visitante_dispositivo_detail'
    ),
    path(
        'dispositivos/<int:pk>/editar/',
        permission_required('unifi_auth_app.change_visitantedispositivo')(
            views.VisitanteDispositivoUpdateView.as_view()
        ),
        name='visitante_dispositivo_update'
    ),
    path(
        'dispositivos/<int:pk>/excluir/',
        permission_required('unifi_auth_app.delete_visitantedispositivo')(
            views.VisitanteDispositivoDeleteView.as_view()
        ),
        name='visitante_dispositivo_delete'
    ),
    path(
        'dispositivos/<int:pk>/toggle-status/',
        permission_required('unifi_auth_app.change_visitantedispositivo')(
            views.VisitanteDispositivoToggleStatusView.as_view()
        ),
        name='visitante_dispositivo_toggle_status'
    ),
    path(
        'api/visitantes/<int:visitante_id>/dispositivos/',
        permission_required('unifi_auth_app.view_visitantedispositivo')(
            views.get_visitante_dispositivos
        ),
        name='api_visitante_dispositivos'
    ),
]

# URLs principais
urlpatterns = [
    # Páginas web
    path('', views.home, name='home'),
    
    # API Endpoints
    path('api/check-auth/', views.check_auth_status, name='check_auth_status'),
    path('api/authorize-visitor/', views.authorize_visitor, name='authorize_visitor'),
    
    # Endpoint antigo (mantido para compatibilidade)
    path('api/authorize-guest/', views.authorize_guest_api, name='authorize_guest_api'),
    
    # URLs de gerenciamento de dispositivos de visitantes
    *[
        path(f'visitantes/{url.pattern._route}', url.callback, name=url.name)
        for url in dispositivo_urls if url.name
    ],
]

# URLs de erro para desenvolvimento
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^400/$', views.bad_request, kwargs={'exception': Exception('Bad Request')}),
        re_path(r'^403/$', views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        re_path(r'^404/$', views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        re_path(r'^500/$', views.server_error),
    ]
