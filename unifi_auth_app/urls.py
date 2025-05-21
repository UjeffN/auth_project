from django.urls import path
from . import views

urlpatterns = [
    # URLs existentes
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/delete/', views.delete_unifi_user, name='user_delete'),

    # URLs do Portal Cativo
    # Rota raiz redireciona para o portal
    path('', views.PortalCativoView.as_view(), name='home'),
    # Mantém a rota /portal/ para compatibilidade
    path('portal/', views.PortalCativoView.as_view(), name='portal_cativo'),
    path('validacao/', views.ValidacaoCodigoView.as_view(), name='validacao_codigo'),
    path('autorizado/', views.acesso_autorizado, name='acesso_autorizado'),
    path('negado/', views.acesso_negado, name='acesso_negado'),
]
