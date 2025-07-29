"""
Middleware para adicionar cabeçalhos de segurança HTTP.
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar cabeçalhos de segurança HTTP.
    """
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__(get_response)

    def process_response(self, request, response):
        """
        Processa a resposta HTTP para adicionar cabeçalhos de segurança.
        """
        # Cabeçalhos de segurança básicos
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy (CSP)
        if hasattr(settings, 'CSP_DIRECTIVES'):
            csp_directives = []
            for directive, sources in settings.CSP_DIRECTIVES.items():
                if sources:
                    csp_directives.append(f"{directive} {' '.join(sources)}")
            if csp_directives:
                response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Permissions Policy (antigo Feature-Policy)
        permissions_policy = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()"
        ]
        response['Permissions-Policy'] = ', '.join(permissions_policy)
        
        return response
