from django.urls import resolve, Resolver404, reverse
from django.http import HttpResponseNotFound, JsonResponse
import logging

logger = logging.getLogger('unifi_auth_app')


class ErrorHandlingMiddleware:
    """
    Middleware para tratamento centralizado de erros.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
        
    def process_exception(self, request, exception):
        """Processa exceções não tratadas."""
        logger.error(
            "Erro não tratado: %s", 
            str(exception), 
            exc_info=True,
            extra={
                'status_code': 500,
                'request': request
            }
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'Ocorreu um erro interno no servidor.'}, 
                status=500
            )
            
        return None  # Deixa o Django lidar com a exceção normalmente


class PortalMiddleware:
    """
    Middleware para controle de acesso ao portal de administração.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Lista de URLs públicas que não requerem autenticação
        self.public_urls = [
            '/api/authorize-visitor/',
            '/api/authorize-guest/',
            '/api/check-auth/'
        ]

    def __call__(self, request):
        # Verifica se é uma tentativa de acessar o admin na porta 8448
        if ':8448' in request.get_host() and request.path.startswith('/admin'):
            return HttpResponseNotFound('Admin interface not available on this port')

        # Verifica se a URL atual está na lista de URLs públicas
        if any(request.path.startswith(url) for url in self.public_urls):
            return self.get_response(request)


        try:
            resolver_match = resolve(request.path)
            if resolver_match.url_name and resolver_match.url_name.startswith('admin:'):
                # Se for uma URL do admin na porta correta, deixa passar
                if ':8449' in request.get_host():
                    return self.get_response(request)
                return HttpResponseNotFound('Admin interface not available on this port')
        except Resolver404:
            pass

        # Se o usuário já estiver autenticado ou estiver acessando a página de login, permite o acesso
        if request.user.is_authenticated or request.path == reverse('login'):
            return self.get_response(request)
            
        # Para todas as outras URLs não autenticadas, redireciona para a página de login
        from django.shortcuts import redirect
        return redirect(f"{reverse('login')}?next={request.path}")
