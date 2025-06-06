from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
from .unifi import UnifiController

# Configurar logging
import logging
logger = logging.getLogger('unifi_auth_app')

@login_required
def home(request):
    """Página inicial do sistema"""
    return render(request, 'unifi_auth_app/home.html', {'title': 'UniFi Auth - Home'})

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
