from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import UniFiUser
from .forms import UniFiUserForm
import requests
from django.conf import settings
from django.contrib import messages

class UserListView(ListView):
    model = UniFiUser
    template_name = 'unifi_auth_app/user_list.html'
    context_object_name = 'users'

class UserCreateView(CreateView):
    model = UniFiUser
    form_class = UniFiUserForm
    template_name = 'unifi_auth_app/user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Autorizar usuário no UniFi Controller
        session = requests.Session()
        login_url = f"{settings.UNIFI_BASE_URL}/api/login"
        auth_url = f"{settings.UNIFI_BASE_URL}/api/s/default/cmd/stamgr"

        try:
            # Autenticação
            session.post(login_url, json={
                "username": settings.UNIFI_USERNAME,
                "password": settings.UNIFI_PASSWORD
            }, verify=False)

            # Autorizar MAC
            session.post(auth_url, json={
                "cmd": "authorize-guest",
                "mac": form.instance.mac_address
            }, verify=False)

            messages.success(self.request, 'Usuário criado e autorizado com sucesso!')
        except Exception as e:
            messages.error(self.request, f'Erro ao autorizar usuário: {str(e)}')
        finally:
            session.get(f"{settings.UNIFI_BASE_URL}/logout")

        return response

def delete_unifi_user(request, user_id):
    try:
        user = UniFiUser.objects.get(id=user_id)
        
        # 1. Excluir via API UniFi
        session = requests.Session()
        login_url = f"{settings.UNIFI_BASE_URL}/api/login"
        delete_url = f"{settings.UNIFI_BASE_URL}/api/s/default/cmd/stamgr"

        # Autenticação
        session.post(login_url, json={
            "username": settings.UNIFI_USERNAME,
            "password": settings.UNIFI_PASSWORD
        }, verify=False)

        # Comando de remoção
        session.post(delete_url, json={
            "cmd": "unauthorize-sta",
            "mac": user.mac_address
        }, verify=False)

        # 2. Excluir do banco
        user.delete()
        messages.success(request, 'Usuário removido com sucesso!')

    except UniFiUser.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
    except Exception as e:
        messages.error(request, f'Erro ao remover usuário: {str(e)}')
    finally:
        if 'session' in locals():
            session.get(f"{settings.UNIFI_BASE_URL}/logout")

    return redirect('user_list')
