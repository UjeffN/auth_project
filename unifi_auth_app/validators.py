"""
Módulo de validações personalizadas para o aplicativo unifi_auth_app.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import format_mac_address

def validate_visitante_mac_address(value):
    """
    Valida e formata um endereço MAC para dispositivos de visitantes.
    
    Args:
        value (str): O endereço MAC a ser validado
        
    Returns:
        str: O endereço MAC formatado
        
    Raises:
        ValidationError: Se o endereço MAC for inválido
    """
    if not value:
        raise ValidationError(_('O endereço MAC é obrigatório'))
    
    try:
        # Usa a função de formatação do modelo para padronizar o MAC
        return format_mac_address(value)
    except ValueError as e:
        raise ValidationError(_('Endereço MAC inválido: %(error)s'), params={'error': str(e)})

# Adicione outras funções de validação personalizadas abaixo, se necessário
