import json
import logging
import time
from datetime import datetime
from django.utils import timezone
from django.conf import settings
import socket

# Configura o logger de auditoria
audit_logger = logging.getLogger('audit')

# Obtém o nome do host para incluir nos logs
HOSTNAME = socket.gethostname()

class APIAuditMiddleware:
    """
    Middleware para registrar requisições de API para fins de auditoria.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignora requisições que não são da API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        try:
            # Captura o corpo da requisição para registro
            request_body = self._get_request_body(request)
            
            # Processa a requisição
            start_time = timezone.now()
            response = self.get_response(request)
            end_time = timezone.now()
            
            # Registra a requisição no log de auditoria
            self._log_request(
                request=request,
                response=response,
                request_body=request_body,
                start_time=start_time,
                end_time=end_time
            )
            
            return response
            
        except Exception as e:
            # Em caso de erro, registra e propaga a exceção
            logger = logging.getLogger('django.request')
            logger.error(
                f"Erro no middleware de auditoria: {str(e)}",
                exc_info=True,
                extra={
                    'status_code': 500,
                    'request': request
                }
            )
            # Propaga a exceção para o próximo middleware/tratador de exceção
            raise
    
    def _get_request_body(self, request):
        """Obtém o corpo da requisição de forma segura."""
        try:
            if request.body:
                if request.content_type == 'application/json':
                    return json.loads(request.body.decode('utf-8'))
                return request.body.decode('utf-8')
        except Exception as e:
            logger.warning(f"Erro ao obter corpo da requisição: {str(e)}")
        return None
    
    def _log_request(self, request, response, request_body, start_time, end_time):
        """Registra a requisição no log de auditoria."""
        try:
            # Calcula o tempo de processamento em milissegundos
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Obtém informações do usuário
            user_info = 'anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"{request.user} (id: {request.user.id})"
            
            # Obtém o IP do cliente
            client_ip = self._get_client_ip(request)
            
            # Prepara os dados do log
            log_data = {
                'timestamp': start_time.isoformat(),
                'hostname': HOSTNAME,
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'user': user_info,
                'client_ip': client_ip,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
            }
            
            # Adiciona o corpo da requisição se existir e for pequeno o suficiente
            if request_body and len(str(request_body)) < 1000:  # Limita o tamanho do log
                log_data['request_body'] = request_body
            
            # Registra no log de auditoria no formato JSON
            audit_logger.info(
                'API Request',
                extra={
                    'audit': log_data
                }
            )
            
        except Exception as e:
            # Se ocorrer um erro ao registrar o log, registra o erro no log do Django
            logger = logging.getLogger('django')
            logger.error(f"Erro ao registrar requisição de auditoria: {str(e)}", exc_info=True)
    
    def _get_client_ip(self, request):
        """Obtém o IP do cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
