import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from .models import Visitante, VisitanteDispositivo
from .unifi import UnifiController
from .forms import VisitanteDispositivoForm

logger = logging.getLogger('unifi_auth_app')

@login_required
def home(request):
    """Página inicial do sistema"""
    return render(
        request,
        'unifi_auth_app/home.html',
        {'title': 'UniFi Auth - Home'}
    )


def get_client_ip(request):
    """
    Obtém o endereço IP do cliente a partir do cabeçalho
    X-Forwarded-For ou REMOTE_ADDR
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_mac_from_ip(ip):
    """Obtém o endereço MAC a partir do IP usando a API do UniFi"""
    try:
        controller = UnifiController()
        if not controller.logged_in and not controller.login():
            return None
            
        url = f"{controller.base_url}/api/s/{controller.site_id}/stat/sta"
        response = controller.session.get(url, timeout=10)
        
        if response.status_code == 200:
            clients = response.json().get('data', [])
            for client in clients:
                if client.get('ip') == ip:
                    return client.get('mac')
    except Exception as e:
        logger.error(f"Erro ao obter MAC do IP {ip}: {str(e)}")
    return None


@csrf_exempt
@require_http_methods(["GET"])
def check_auth_status(request):
    """Verifica se o IP atual precisa de autenticação"""
    client_ip = get_client_ip(request)
    if not client_ip:
        return JsonResponse({'error': 'Não foi possível determinar o endereço IP'}, status=400)
    
    # Verifica se já existe um visitante autorizado com este IP
    visitante = Visitante.objects.filter(ip_address=client_ip, autorizado=True).first()
    if visitante:
        return JsonResponse({
            'status': 'authorized',
            'message': 'Usuário já autorizado',
            'data': {
                'nome': visitante.nome,
                'email': visitante.email,
                'data_acesso': visitante.data_acesso.isoformat()
            }
        })
    
    # Tenta obter o MAC address do cliente
    mac_address = get_mac_from_ip(client_ip)
    
    return JsonResponse({
        'status': 'unauthorized',
        'requires_auth': True,
        'ip': client_ip,
        'mac': mac_address
    })


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def authorize_visitor(request):
    """Endpoint para autorizar um visitante na rede"""
    logger.info(f"Requisição recebida: {request.method} {request.path}")
    logger.info(f"Cabeçalhos: {dict(request.headers)}")
    
    # Configura os cabeçalhos CORS
    if request.method == "OPTIONS":
        logger.info("Resposta OPTIONS enviada")
        response = JsonResponse({}, status=200)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With, X-CSRFToken, X-Original-IP"
        response["Access-Control-Expose-Headers"] = "Content-Length, Content-Range"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Max-Age"] = "86400"  # 24 horas
        return response
        
    try:
        logger.info(f"Corpo da requisição: {request.body}")
        data = json.loads(request.body)
        logger.info(f"Dados decodificados: {data}")
        
        # Validação dos dados
        required_fields = ['nome', 'email', 'telefone']
        if not all(field in data for field in required_fields):
            response = JsonResponse(
                {'success': False, 'error': 'Campos obrigatórios faltando'}, 
                status=400
            )
            response["Access-Control-Allow-Origin"] = "*"
            return response
        
        # Obtém o IP do cliente
        client_ip = data.get('client_ip') or get_client_ip(request)
        
        # Tenta obter o MAC do cliente se não foi fornecido
        mac_address = data.get('mac_address')
        if not mac_address:
            mac_address = get_mac_from_ip(client_ip)
            if not mac_address:
                response = JsonResponse(
                    {'success': False, 'error': 'Não foi possível obter o endereço MAC do dispositivo'}, 
                    status=400
                )
                response["Access-Control-Allow-Origin"] = "*"
                return response
        
        # Cria o registro do visitante
        try:
            visitante = Visitante.objects.create(
                nome=data['nome'],
                email=data['email'],
                telefone=data['telefone'],
                mac_address=mac_address,
                ip_address=client_ip,
                autorizado=True
            )
        except Exception as e:
            logger.error(f"Erro ao criar registro do visitante: {str(e)}")
            response = JsonResponse(
                {'success': False, 'error': 'Erro ao processar os dados do visitante'}, 
                status=500
            )
            response["Access-Control-Allow-Origin"] = "*"
            return response
        
        # Autoriza o dispositivo no UniFi
        try:
            controller = UnifiController()
            if controller.login():
                # Tenta obter o AP do cliente
                ap_mac = data.get('ap_mac')
                if not ap_mac:
                    # Se o AP não foi fornecido, tenta obter da API do UniFi
                    try:
                        client_info = controller.get_client_info(mac_address)
                        if client_info and 'ap_mac' in client_info:
                            ap_mac = client_info['ap_mac']
                    except Exception as e:
                        logger.warning(f"Não foi possível obter informações do cliente: {str(e)}")
                
                # Se tem o AP, tenta autorizar
                if ap_mac:
                    minutes = int(data.get('minutes', 1440))  # 24h por padrão
                    success = controller.authorize_guest(mac_address, ap_mac, minutes=minutes)
                    if not success:
                        logger.error(f"Falha ao autorizar o dispositivo {mac_address} no AP {ap_mac}")
                else:
                    logger.warning("AP MAC não encontrado, pulando autorização no UniFi")
        except Exception as e:
            logger.error(f"Erro ao autorizar no UniFi Controller: {str(e)}")
            # Não retorna erro, pois o registro do visitante já foi criado
        
        # Monta a resposta de sucesso
        response_data = {
            'success': True,
            'message': 'Visitante autorizado com sucesso',
            'redirect': data.get('redirect_url', 'http://www.google.com'),
            'data': {
                'id': visitante.id,
                'nome': visitante.nome,
                'email': visitante.email,
                'data_acesso': visitante.data_acesso.isoformat()
            }
        }
        
        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"
        return response
        
    except json.JSONDecodeError:
        response = JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Erro ao autorizar visitante: {str(e)}")
        response = JsonResponse(
            {'success': False, 'error': 'Erro interno do servidor'}, 
            status=500
        )
        response["Access-Control-Allow-Origin"] = "*"
        return response

@csrf_exempt
def authorize_guest_api(request):
    """
    API endpoint para autorizar um convidado no UniFi Controller.
    Espera um POST com os seguintes parâmetros:
    - name: Nome do visitante
    - email: Email do visitante
    - phone: Telefone do visitante
    - client_ip: IP do cliente
    - client_mac: MAC address do cliente
    - ap_mac: MAC address do AP (opcional, será obtido automaticamente se não fornecido)
    - minutes: Duração do acesso em minutos (opcional, padrão 1440 - 24h)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        
        # Dados obrigatórios
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        client_ip = data.get('client_ip')
        client_mac = data.get('client_mac')
        
        # Dados opcionais
        ap_mac = data.get('ap_mac')
        minutes = int(data.get('minutes', 1440))  # 24 horas por padrão
        
        # Validação dos campos obrigatórios
        if not all([name, email, client_ip, client_mac]):
            return JsonResponse({
                'error': 'Campos obrigatórios faltando',
                'required': ['name', 'email', 'client_ip', 'client_mac']
            }, status=400)
            
        # Se o MAC do AP não foi fornecido, tenta obter do cliente conectado
        if not ap_mac:
            try:
                controller = UnifiController()
                if controller.login():
                    client_info = controller.get_client_info(client_mac)
                    if client_info and 'ap_mac' in client_info:
                        ap_mac = client_info['ap_mac']
            except Exception as e:
                logger.warning(f"Não foi possível obter o AP do cliente: {str(e)}")
        
        if not ap_mac:
            return JsonResponse({
                'error': 'Não foi possível determinar o AP do cliente. Por favor, tente novamente.'
            }, status=400)
        
        # Cria o registro do visitante
        try:
            visitante = Visitante.objects.create(
                nome=name,
                email=email,
                telefone=phone,
                mac_address=client_mac,
                ip_address=client_ip,
                autorizado=True
            )
            
            # Autoriza o dispositivo no UniFi
            controller = UnifiController()
            if controller.login():
                success = controller.authorize_guest(client_mac, ap_mac, minutes=minutes)
                if not success:
                    logger.error(f"Falha ao autorizar o dispositivo {client_mac} no AP {ap_mac}")
                    return JsonResponse({
                        'error': 'Falha ao autorizar o dispositivo na rede',
                        'success': False
                    }, status=500)
            
            return JsonResponse({
                'success': True,
                'message': 'Dispositivo autorizado com sucesso',
                'redirect': 'http://www.google.com'  # URL para redirecionamento após sucesso
            })
            
        except Exception as e:
            logger.error(f"Erro ao criar registro do visitante: {str(e)}")
            return JsonResponse({
                'error': 'Erro ao processar a solicitação',
                'details': str(e),
                'success': False
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Formato de dados inválido',
            'success': False
        }, status=400)
        
    except Exception as e:
        logger.error(f"Erro na API de autorização: {str(e)}")
        return JsonResponse({
            'error': 'Erro interno do servidor',
            'success': False
        }, status=500)


# ============================================
# Views para Gerenciamento de Dispositivos de Visitantes
# ============================================

class VisitanteDispositivoListView(LoginRequiredMixin, ListView):
    """Lista todos os dispositivos de visitantes"""
    model = VisitanteDispositivo
    template_name = 'unifi_auth_app/visitante_dispositivo/visitantedispositivo_list.html'
    context_object_name = 'dispositivos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('visitante')
        
        # Filtro por termo de busca
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(visitante_mac_address__icontains=search) |
                Q(visitante_nome_dispositivo__icontains=search) |
                Q(visitante__nome__icontains=search) |
                Q(visitante__email__icontains=search)
            )
        
        # Filtro por status de ativação
        status = self.request.GET.get('status')
        if status == 'ativo':
            queryset = queryset.filter(visitante_dispositivo_ativo=True)
        elif status == 'inativo':
            queryset = queryset.filter(visitante_dispositivo_ativo=False)
        
        return queryset.order_by('-visitante_ultimo_acesso')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_ativos'] = VisitanteDispositivo.objects.filter(visitante_dispositivo_ativo=True).count()
        context['total_inativos'] = VisitanteDispositivo.objects.filter(visitante_dispositivo_ativo=False).count()
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context


class VisitanteDispositivoCreateView(LoginRequiredMixin, CreateView):
    """Adiciona um novo dispositivo de visitante"""
    model = VisitanteDispositivo
    form_class = VisitanteDispositivoForm
    template_name = 'unifi_auth_app/visitante_dispositivo/visitantedispositivo_form.html'
    success_url = reverse_lazy('unifi_auth_app:visitante_dispositivo_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Dispositivo adicionado com sucesso!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Adicionar Dispositivo de Visitante'
        return context


class VisitanteDispositivoUpdateView(LoginRequiredMixin, UpdateView):
    """Atualiza um dispositivo de visitante existente"""
    model = VisitanteDispositivo
    form_class = VisitanteDispositivoForm
    template_name = 'unifi_auth_app/visitante_dispositivo/visitantedispositivo_form.html'
    success_url = reverse_lazy('unifi_auth_app:visitante_dispositivo_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Dispositivo atualizado com sucesso!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Dispositivo: {self.object.visitante_mac_address}'
        return context


class VisitanteDispositivoDetailView(LoginRequiredMixin, DetailView):
    """Exibe os detalhes de um dispositivo de visitante"""
    model = VisitanteDispositivo
    template_name = 'unifi_auth_app/visitante_dispositivo/visitantedispositivo_detail.html'
    context_object_name = 'dispositivo'


@method_decorator(csrf_exempt, name='dispatch')
class VisitanteDispositivoToggleStatusView(LoginRequiredMixin, UpdateView):
    """Ativa/desativa um dispositivo de visitante"""
    model = VisitanteDispositivo
    fields = []  # Não precisamos de campos, apenas atualizar o status
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verifica se o usuário tem permissão para desativar/ativar
        if not request.user.has_perm('unifi_auth_app.change_visitantedispositivo'):
            return JsonResponse(
                {'error': 'Você não tem permissão para realizar esta ação'}, 
                status=403
            )
        
        # Alterna o status do dispositivo
        self.object.visitante_dispositivo_ativo = not self.object.visitante_dispositivo_ativo
        self.object.save()
        
        action = 'ativado' if self.object.visitante_dispositivo_ativo else 'desativado'
        return JsonResponse({
            'status': 'success',
            'message': f'Dispositivo {action} com sucesso!',
            'is_active': self.object.visitante_dispositivo_ativo
        })


class VisitanteDispositivoDeleteView(LoginRequiredMixin, DeleteView):
    """Remove permanentemente um dispositivo de visitante"""
    model = VisitanteDispositivo
    template_name = 'unifi_auth_app/visitante_dispositivo/visitantedispositivo_confirm_delete.html'
    success_url = reverse_lazy('unifi_auth_app:visitante_dispositivo_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Dispositivo removido com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
def get_visitante_dispositivos(request, visitante_id):
    """Retorna a lista de dispositivos de um visitante em formato JSON"""
    try:
        visitante = get_object_or_404(Visitante, pk=visitante_id)
        dispositivos = visitante.visitante_dispositivos.all().order_by(
            '-visitante_dispositivo_ativo',
            'visitante_nome_dispositivo'
        )
        
        data = [
            {
                'id': d.id,
                'nome': d.visitante_nome_dispositivo or 'Dispositivo sem nome',
                'mac': d.visitante_mac_address,
                'ativo': d.visitante_dispositivo_ativo,
                'data_cadastro': d.visitante_data_cadastro.strftime('%d/%m/%Y %H:%M'),
                'ultimo_acesso': (
                    d.visitante_ultimo_acesso.strftime('%d/%m/%Y %H:%M')
                    if d.visitante_ultimo_acesso
                    else 'Nunca'
                )
            }
            for d in dispositivos
        ]
        
        return JsonResponse({'status': 'success', 'data': data})
        
    except Exception as e:
        logger.error(
            "Erro ao buscar dispositivos do visitante %s: %s",
            visitante_id,
            str(e)
        )
        return JsonResponse(
            {'status': 'error', 'message': 'Erro ao buscar dispositivos'},
            status=500
        )


# ============================================
# Views de Manipulação de Erros Personalizadas
# ============================================

def bad_request(request, exception=None, template_name='unifi_auth_app/visitante_dispositivo/400.html'):
    """View personalizada para erro 400 (Bad Request)"""
    return render(
        request,
        template_name,
        {
            'error': '400 - Requisição inválida',
            'message': 'A requisição não pôde ser processada.'
        },
        status=400
    )


def permission_denied(request, exception=None, template_name='unifi_auth_app/visitante_dispositivo/403.html'):
    """View personalizada para erro 403 (Forbidden)"""
    return render(
        request,
        template_name,
        {
            'error': '403 - Acesso negado',
            'message': 'Você não tem permissão para acessar esta página.'
        },
        status=403
    )


def page_not_found(request, exception=None, template_name='unifi_auth_app/visitante_dispositivo/404.html'):
    """View personalizada para erro 404 (Not Found)"""
    return render(
        request,
        template_name,
        {
            'error': '404 - Página não encontrada',
            'message': 'A página que você está procurando não existe ou foi movida.'
        },
        status=404
    )


def server_error(request, template_name='unifi_auth_app/visitante_dispositivo/500.html'):
    """View personalizada para erro 500 (Internal Server Error)"""
    return render(
        request,
        template_name,
        {
            'error': '500 - Erro no servidor',
            'message': 'Ocorreu um erro inesperado no servidor.'
        },
        status=500
    )


def csrf_failure(request, reason="", template_name='unifi_auth_app/visitante_dispositivo/403_csrf.html'):
    """View personalizada para falha de validação CSRF"""
    return render(
        request,
        template_name,
        {
            'error': '403 - Token CSRF inválido',
            'message': 'A sessão expirou ou o token CSRF é inválido.'
        },
        status=403
    )
