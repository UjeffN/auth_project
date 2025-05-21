from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, FormView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.mail import send_mail
import logging
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from .models import UniFiUser, Visitante, CodigoValidacao, AcessoVisitante
from .forms import UniFiUserForm, VisitanteForm, CodigoValidacaoForm
from .unifi_api import UniFiControllerAPI
import random
import string
import requests
from ipware import get_client_ip

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

# === Views do Portal Cativo ===

def get_mac_from_ip(ip_address):
    """Tenta obter o MAC address a partir do IP usando o UniFi Controller"""
    try:
        from .unifi_guest_api import UniFiGuestAPI
        import socket
        socket.setdefaulttimeout(5)  # Timeout de 5 segundos
        
        with UniFiGuestAPI() as unifi:
            return unifi.get_mac_from_ip(ip_address)
    except Exception as e:
        logging.error(f'Erro ao obter MAC do IP {ip_address}: {str(e)}')
        return None

def gerar_codigo():
    """Gera um código numérico de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

def enviar_codigo_email(visitante, codigo):
    """Envia o código de validação por email"""
    try:
        subject = 'Código de Verificação - Câmara Municipal de Parauapebas'
        html_message = render_to_string('unifi_auth_app/email/codigo_acesso.html', {
            'visitante': visitante,
            'codigo': codigo
        })
        send_mail(
            subject,
            f'Seu código de acesso é: {codigo}',  # Versão texto plano
            settings.DEFAULT_FROM_EMAIL,
            [visitante.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logging.error(f'Erro ao enviar email para {visitante.email}: {str(e)}')
        return False

class PortalCativoView(FormView):
    template_name = 'unifi_auth_app/portal_cativo.html'
    form_class = VisitanteForm
    success_url = reverse_lazy('validacao_codigo')

    def get_client_ip(self):
        client_ip, _ = get_client_ip(self.request)
        return client_ip

    def form_valid(self, form):
        visitante = form.save(commit=False)
        visitante.save()

        # Verifica limite de acessos por dia
        hoje = timezone.now().date()
        acessos_hoje = AcessoVisitante.objects.filter(
            visitante=visitante,
            data_autorizacao__date=hoje
        ).count()

        if acessos_hoje >= settings.PORTAL_CATIVO['limite_acessos_dia']:
            messages.error(
                self.request,
                'Você já atingiu o limite de acessos diários.'
            )
            return self.form_invalid(form)

        # Obtém o MAC address do cliente
        ip_address = self.get_client_ip()
        if not ip_address:
            messages.error(
                self.request,
                'Não foi possível identificar seu dispositivo. Por favor, tente novamente.'
            )
            return self.form_invalid(form)

        mac_address = get_mac_from_ip(ip_address)
        if not mac_address:
            messages.error(
                self.request,
                'Não foi possível identificar seu dispositivo. '
                'Certifique-se de que está conectado à rede.'
            )
            return self.form_invalid(form)

        # Gera o código
        codigo = gerar_codigo()
        validacao = CodigoValidacao.objects.create(
            visitante=visitante,
            codigo=codigo,
            ip_address=ip_address,
            mac_address=mac_address
        )

        # Tenta enviar o código por email
        logger = logging.getLogger('django')
        logger.info(f'Tentando enviar código para {visitante.email}')
        
        if not enviar_codigo_email(visitante, codigo):
            # Se falhar, exclui o código gerado e retorna erro
            validacao.delete()
            messages.error(
                self.request,
                'Não foi possível enviar o código para seu email. '
                'Por favor, verifique se o email está correto e tente novamente.'
            )
            return self.form_invalid(form)

        logger.info('Email enviado com sucesso')
        messages.success(
            self.request,
            'Código de validação enviado para seu email. '
            'Por favor, verifique sua caixa de entrada e spam.'
        )

        # Salva o ID do visitante na sessão
        self.request.session['visitante_id'] = visitante.id
        return super().form_valid(form)

class ValidacaoCodigoView(FormView):
    template_name = 'unifi_auth_app/validacao_codigo.html'
    form_class = CodigoValidacaoForm
    success_url = reverse_lazy('acesso_autorizado')

    def get(self, request, *args, **kwargs):
        if 'visitante_id' not in request.session:
            return redirect('portal_cativo')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        visitante_id = self.request.session.get('visitante_id')
        if not visitante_id:
            messages.error(self.request, 'Sessão expirada. Preencha o formulário novamente.')
            return redirect('portal_cativo')

        visitante = get_object_or_404(Visitante, id=visitante_id)
        codigo = form.cleaned_data['codigo']
        ip_address = get_client_ip(self.request)[0]

        # Tenta obter o MAC address do cliente atual
        mac_address = get_mac_from_ip(ip_address)
        if not mac_address:
            messages.error(
                self.request,
                'Não foi possível identificar seu dispositivo.'
            )
            return redirect('acesso_negado')

        try:
            # Busca o código de validação
            validacao = CodigoValidacao.objects.get(
                visitante=visitante,
                codigo=codigo,
                mac_address=mac_address,  # Verifica se é o mesmo dispositivo
                validado=False
            )

            # Verifica se expirou
            if validacao.expirado:
                messages.error(self.request, 'Código expirado.')
                return self.form_invalid(form)

        except CodigoValidacao.DoesNotExist:
            messages.error(
                self.request,
                'Código inválido ou deve ser usado no mesmo dispositivo que o solicitou.'
            )
            return self.form_invalid(form)

        # Marca o código como validado
        validacao.validado_em = timezone.now()
        validacao.save()

        # Tenta obter o MAC address
        mac_address = get_mac_from_ip(ip_address)
        if not mac_address:
            messages.warning(
                self.request,
                'Não foi possível identificar seu dispositivo. Entre em contato com o suporte.'
            )
            return redirect('acesso_negado')

        # Atualiza o MAC do visitante
        visitante.mac_address = mac_address
        visitante.save()

        # Cria o registro de acesso
        expiracao = timezone.now() + timezone.timedelta(
            hours=settings.PORTAL_CATIVO['acesso_expiracao_horas']
        )
        AcessoVisitante.objects.create(
            visitante=visitante,
            mac_address=mac_address,
            ip_address=ip_address,
            codigo_validacao=validacao,
            data_expiracao=expiracao
        )

        # Autoriza o MAC no UniFi
        try:
            from .unifi_guest_api import UniFiGuestAPI
            with UniFiGuestAPI() as unifi:
                unifi.authorize_guest(mac_address, minutes=60)
            messages.success(self.request, 'Acesso autorizado com sucesso!')
        except Exception as e:
            messages.error(
                self.request,
                'Erro ao autorizar acesso. Entre em contato com o suporte.'
            )
            return redirect('acesso_negado')

        return super().form_valid(form)

def acesso_autorizado(request):
    if 'visitante_id' not in request.session:
        return redirect('portal_cativo')

    visitante = get_object_or_404(Visitante, id=request.session['visitante_id'])
    del request.session['visitante_id']  # Limpa a sessão

    return render(request, 'unifi_auth_app/acesso_autorizado.html', {
        'visitante': visitante
    })

def acesso_negado(request):
    return render(request, 'unifi_auth_app/acesso_negado.html')
