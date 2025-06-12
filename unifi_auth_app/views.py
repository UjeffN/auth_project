from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
import json
import requests
from .models import Visitante
from .unifi import UnifiController

# Configurar logging
import logging
logger = logging.getLogger('unifi_auth_app')

@login_required
def home(request):
    """Página inicial do sistema"""
    return render(request, 'unifi_auth_app/home.html', {'title': 'UniFi Auth - Home'})


def get_client_ip(request):
    """Obtém o endereço IP do cliente a partir do cabeçalho X-Forwarded-For ou REMOTE_ADDR"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_mac_from_ip(ip):
    """Obtém o endereço MAC a partir do IP usando a API do UniFi"""
    try:
        controller = UnifiController()
        if not controller.logged_in and not controller.login():
            return None
            
        url = f"{controller.base_url}/api/s/{controller.site_id}/stat/sta"
        response = controller.session.get(url)
        
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
@require_http_methods(["POST"])
def authorize_visitor(request):
    """Endpoint para autorizar um visitante na rede"""
    try:
        data = json.loads(request.body)
        
        # Validação dos dados
        required_fields = ['nome', 'email', 'telefone', 'mac_address']
        if not all(field in data for field in required_fields):
            return JsonResponse(
                {'error': 'Campos obrigatórios faltando'}, 
                status=400
            )
        
        # Obtém o IP do cliente
        client_ip = get_client_ip(request)
        
        # Cria o registro do visitante
        visitante = Visitante.objects.create(
            nome=data['nome'],
            email=data['email'],
            telefone=data['telefone'],
            mac_address=data['mac_address'],
            ip_address=client_ip,
            autorizado=True
        )
        
        # Autoriza o dispositivo no UniFi
        controller = UnifiController()
        if controller.login():
            # Obtém o AP mais próximo do cliente para autorização
            url = f"{controller.base_url}/api/s/{controller.site_id}/stat/sta/{data['mac_address']}"
            response = controller.session.get(url)
            
            if response.status_code == 200:
                client_data = response.json().get('data', [{}])[0]
                ap_mac = client_data.get('ap_mac')
                
                if ap_mac:
                    # Autoriza o dispositivo por 24 horas
                    controller.authorize_guest(data['mac_address'], ap_mac, minutes=1440)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Visitante autorizado com sucesso',
            'data': {
                'id': visitante.id,
                'nome': visitante.nome,
                'email': visitante.email,
                'data_acesso': visitante.data_acesso.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao autorizar visitante: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@csrf_exempt
def authorize_guest_api(request):
    """
    API endpoint para autorizar um convidado no UniFi Controller.
    Espera um POST com os seguintes parâmetros:
    - mac: MAC address do cliente
    - ap_mac: MAC address do AP
    - minutes: Duração do acesso em minutos (opcional, padrão 60)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        mac = data.get('mac')
        ap_mac = data.get('ap_mac')
        minutes = data.get('minutes', 60)

        if not all([mac, ap_mac]):
            return JsonResponse({'error': 'MAC address do cliente e do AP são obrigatórios'}, status=400)

        # Instancia o controlador UniFi
        controller = UnifiController()
        
        # Autoriza o dispositivo
        controller.authorize_guest(mac, ap_mac, minutes=minutes)

        return JsonResponse({
            'status': 'success',
            'message': 'Cliente autorizado com sucesso'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao autorizar cliente: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
