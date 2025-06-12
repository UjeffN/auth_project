"""
Middleware para medir e registrar o tempo de resposta das requisições.
"""
import time
import logging
from django.conf import settings

logger = logging.getLogger('performance')

class RequestTimingMiddleware:
    """
    Middleware para medir e registrar o tempo de resposta das requisições.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignora requisições estáticas e de admin por padrão
        if self._should_skip_request(request):
            return self.get_response(request)
        
        # Inicia o timer
        start_time = time.time()
        
        # Processa a requisição
        response = self.get_response(request)
        
        # Calcula o tempo de resposta
        total_time = time.time() - start_time
        
        # Registra o tempo de resposta se for maior que o limiar configurado
        slow_request_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)  # 1 segundo por padrão
        
        if total_time > slow_request_threshold:
            logger.warning(
                'Slow request: %s %s (%.2f seconds)',
                request.method,
                request.path,
                total_time,
                extra={
                    'request': request,
                    'total_time': total_time,
                    'status_code': response.status_code,
                }
            )
        
        # Adiciona o tempo de resposta no cabeçalho para depuração
        if getattr(settings, 'SHOW_REQUEST_TIME_HEADER', False):
            response['X-Request-Time'] = f"{total_time:.2f}s"
        
        return response
    
    def _should_skip_request(self, request):
        """
        Verifica se a requisição deve ser ignorada pelo middleware.
        """
        # Lista de caminhos a serem ignorados
        ignored_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/__debug__/',
            '/admin/',
        ]
        
        return any(request.path.startswith(path) for path in ignored_paths)
