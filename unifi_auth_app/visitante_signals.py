from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Visitante
from .unifi_api import UniFiControllerAPI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_unifi_api() -> UniFiControllerAPI:
    """Retorna uma instância configurada da API do UniFi para visitantes"""
    base_url = f'https://{settings.UNIFI_CONTROLLER_CONFIG["IP"]}:{settings.UNIFI_CONTROLLER_CONFIG["PORT"]}'
    return UniFiControllerAPI(
        base_url=base_url,
        site=settings.UNIFI_CONTROLLER_CONFIG['SITE_ID'],
        username=settings.UNIFI_CONTROLLER_CONFIG['USERNAME'],
        password=settings.UNIFI_CONTROLLER_CONFIG['PASSWORD'],
        verify_ssl=False
    )

@receiver(post_save, sender=Visitante)
def autorizar_visitante_no_unifi(sender, instance, created, **kwargs):
    """Signal handler para autorizar um visitante quando ele é criado ou atualizado"""
    if not instance.mac_address or not instance.autorizado:
        return

    try:
        logger.info(f"[SIGNAL] Visitante {'criado' if created else 'atualizado'}: {instance.nome} - {instance.mac_address}")
        
        # Usa o SSID específico para visitantes, ou o padrão se não estiver configurado
        ssid_visitantes = getattr(settings, 'UNIFI_SSID_VISITANTES', 'Câmara')
        
        api = get_unifi_api()
        resposta = api.add_mac_to_ssid_whitelist(instance.mac_address, ssid_name=ssid_visitantes)
        logger.info(f"[UNI-FI] Visitante {instance.nome} - MAC {instance.mac_address} adicionado à whitelist do SSID '{ssid_visitantes}': {resposta}")

    except Exception as e:
        logger.error(f"[ERRO UNI-FI] Falha ao autorizar visitante {instance.nome} - MAC {instance.mac_address}: {str(e)}")

@receiver(post_delete, sender=Visitante)
def desautorizar_visitante_no_unifi(sender, instance, **kwargs):
    """Signal handler para desautorizar um visitante quando ele é removido"""
    if not instance.mac_address:
        return
        
    try:
        logger.info(f"[SIGNAL] Visitante removido: {instance.nome} - {instance.mac_address}")
        
        # Usa o SSID específico para visitantes, ou o padrão se não estiver configurado
        ssid_visitantes = getattr(settings, 'UNIFI_SSID_VISITANTES', 'Câmara')
        
        api = get_unifi_api()
        resposta = api.remove_mac_from_ssid_whitelist(instance.mac_address, ssid_name=ssid_visitantes)
        logger.info(f"[UNI-FI] Visitante {instance.nome} - MAC {instance.mac_address} removido da whitelist do SSID '{ssid_visitantes}': {resposta}")
    except Exception as e:
        logger.error(f"[ERRO UNI-FI] Falha ao remover visitante {instance.nome} - MAC {instance.mac_address}: {e}")
