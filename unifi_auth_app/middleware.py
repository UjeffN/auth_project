from django.urls import resolve, Resolver404
from django.http import HttpResponseNotFound

class PortalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verifica se é uma tentativa de acessar o admin na porta 8448
        if ':8448' in request.get_host() and request.path.startswith('/admin'):
            return HttpResponseNotFound('Admin interface not available on this port')

        try:
            resolver_match = resolve(request.path)
            if resolver_match.url_name and resolver_match.url_name.startswith('admin:'):
                # Se for uma URL do admin na porta correta, deixa passar
                if ':8449' in request.get_host():
                    return self.get_response(request)
                return HttpResponseNotFound('Admin interface not available on this port')
        except Resolver404:
            pass

        # Para todas as outras URLs, força o uso das URLs do portal
        from unifi_auth_app.views import portal_login
        return portal_login(request)
