from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.db.models import QuerySet
from .models import Dispositivo, UniFiUser
from .unifi_api import UniFiControllerAPI
from django.conf import settings
from typing import List
import logging

logger = logging.getLogger(__name__)

def get_unifi_api() -> UniFiControllerAPI:
    """Retorna uma instância configurada da API do UniFi"""
    base_url = f'https://{settings.UNIFI_CONTROLLER_CONFIG["IP"]}:{settings.UNIFI_CONTROLLER_CONFIG["PORT"]}'
    return UniFiControllerAPI(
        base_url=base_url,
        site=settings.UNIFI_CONTROLLER_CONFIG['SITE_ID'],
        username=settings.UNIFI_CONTROLLER_CONFIG['USERNAME'],
        password=settings.UNIFI_CONTROLLER_CONFIG['PASSWORD'],
        verify_ssl=False
    )

@receiver(post_save, sender=Dispositivo)
def autorizar_dispositivo_no_unifi(sender, instance, created, **kwargs):
    """Signal handler para autorizar um dispositivo quando ele é criado ou atualizado"""
    if not instance.mac_address:
        logger.warning(f"[SIGNAL] Dispositivo sem MAC address")
        return

    if not instance.usuario:
        logger.warning(f"[SIGNAL] Dispositivo sem usuário associado")
        return

    try:
        nome_usuario = instance.usuario.nome
        logger.info(f"[SIGNAL] Dispositivo atualizado: {instance.mac_address} do usuário {nome_usuario}")

        api = get_unifi_api()
        resposta = api.add_mac_to_ssid_whitelist(instance.mac_address, ssid_name="Câmara")
        logger.info(f"[UNI-FI] MAC {instance.mac_address} adicionado à whitelist do SSID 'Câmara': {resposta}")

    except Exception as e:
        logger.error(f"[ERRO UNI-FI] Falha ao autorizar MAC {instance.mac_address}: {str(e)}")

@receiver(post_delete, sender=Dispositivo)
def desautorizar_dispositivo_no_unifi(sender, instance, **kwargs):
    """Signal handler para desautorizar um dispositivo quando ele é excluído"""
    try:
        logger.info(f"[SIGNAL] Dispositivo removido: {instance.mac_address} do usuário {instance.usuario.nome}")
        api = get_unifi_api()
        resposta = api.remove_mac_from_ssid_whitelist(instance.mac_address, ssid_name="Câmara")
        logger.info(f"[UNI-FI] MAC {instance.mac_address} removido da whitelist do SSID 'Câmara': {resposta}")
    except Exception as e:
        logger.error(f"[ERRO UNI-FI] Falha ao remover MAC {instance.mac_address}: {e}")

@receiver(post_save, sender=UniFiUser)
def atualizar_dispositivos_em_lote(sender, instance, created, **kwargs):
    """Signal handler para atualizar múltiplos dispositivos de uma vez quando a relação M2M é modificada"""
    try:
        api = get_unifi_api()
        dispositivos = instance.dispositivos.all()
        macs = [d.mac_address for d in dispositivos if d.mac_address]

        if not macs:
            return

        # Atualiza todos os MACs do usuário
        resposta = api.bulk_add_macs_to_ssid_whitelist(macs, ssid_name="Câmara")
        logger.info(f"[UNI-FI] {len(macs)} MACs do usuário {instance.nome} atualizados na whitelist do SSID 'Câmara': {resposta}")

    except Exception as e:
        logger.error(f"[ERRO UNI-FI] Falha ao atualizar MACs em lote: {str(e)}")
