from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Dispositivo
from .unifi_api import UniFiControllerAPI

@receiver(post_save, sender=Dispositivo)
def autorizar_dispositivo_no_unifi(sender, instance, created, **kwargs):
    if created:
        print(f"[SIGNAL] Novo dispositivo criado: {instance.mac_address} do usuário {instance.usuario.nome}")
        api = UniFiControllerAPI()
        try:
            resposta = api.add_mac_to_ssid_whitelist(instance.mac_address, ssid_name="Câmara")
            print(f"[UNI-FI] MAC {instance.mac_address} adicionado à whitelist do SSID 'Câmara': {resposta}")
        except Exception as e:
            print(f"[ERRO UNI-FI] Falha ao autorizar MAC {instance.mac_address}: {e}")

@receiver(post_delete, sender=Dispositivo)
def desautorizar_dispositivo_no_unifi(sender, instance, **kwargs):
    print(f"[SIGNAL] Dispositivo removido: {instance.mac_address} do usuário {instance.usuario.nome}")
    api = UniFiControllerAPI()
    try:
        resposta = api.remove_mac_from_ssid_whitelist(instance.mac_address, ssid_name="Câmara")
        print(f"[UNI-FI] MAC {instance.mac_address} removido da whitelist do SSID 'Câmara': {resposta}")
    except Exception as e:
        print(f"[ERRO UNI-FI] Falha ao remover MAC {instance.mac_address}: {e}")
