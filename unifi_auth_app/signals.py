from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Dispositivo
from .unifi_api import UniFiControllerAPI
from django.conf import settings

@receiver(post_save, sender=Dispositivo)
def autorizar_dispositivo_no_unifi(sender, instance, created, **kwargs):
    if not created:
        return

    if not instance.mac_address:
        print(f"[SIGNAL] Dispositivo sem MAC address")
        return

    if not instance.usuario:
        print(f"[SIGNAL] Dispositivo sem usuário associado")
        return

    try:
        nome_usuario = instance.usuario.nome
        print(f"[SIGNAL] Novo dispositivo criado: {instance.mac_address} do usuário {nome_usuario}")

        # Construindo a URL base
        base_url = f'https://{settings.UNIFI_CONTROLLER_CONFIG["IP"]}:{settings.UNIFI_CONTROLLER_CONFIG["PORT"]}'
        
        api = UniFiControllerAPI(
            base_url=base_url,
            site=settings.UNIFI_CONTROLLER_CONFIG['SITE_ID'],
            username=settings.UNIFI_CONTROLLER_CONFIG['USERNAME'],
            password=settings.UNIFI_CONTROLLER_CONFIG['PASSWORD'],
            verify_ssl=False
        )

        resposta = api.add_mac_to_ssid_whitelist(instance.mac_address, ssid_name="Câmara")
        print(f"[UNI-FI] MAC {instance.mac_address} adicionado à whitelist do SSID 'Câmara': {resposta}")

    except Exception as e:
        print(f"[ERRO UNI-FI] Falha ao autorizar MAC {instance.mac_address}: {str(e)}")

@receiver(post_delete, sender=Dispositivo)
def desautorizar_dispositivo_no_unifi(sender, instance, **kwargs):
    print(f"[SIGNAL] Dispositivo removido: {instance.mac_address} do usuário {instance.usuario.nome}")
    api = UniFiControllerAPI()
    try:
        resposta = api.remove_mac_from_ssid_whitelist(instance.mac_address, ssid_name="Câmara")
        print(f"[UNI-FI] MAC {instance.mac_address} removido da whitelist do SSID 'Câmara': {resposta}")
    except Exception as e:
        print(f"[ERRO UNI-FI] Falha ao remover MAC {instance.mac_address}: {e}")
