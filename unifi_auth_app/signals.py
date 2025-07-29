from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UnifiUserStatus
from .unifi_api import UniFiControllerAPI  # ajuste esse import conforme seu projeto
from django.utils.timezone import now

@receiver(post_save, sender=User)
def cadastrar_no_unifi(sender, instance, created, **kwargs):
    if created:
        print(f"[SIGNAL] Novo usuário criado: {instance.username}")
        api = UniFiControllerAPI()
        try:
            sucesso = api.criar_usuario(instance.username)  # ou o método que você implementou
            if sucesso:
                UnifiUserStatus.objects.create(
                    user=instance,
                    cadastrado_unifi=True,
                    data_cadastro=now()
                )
                print(f"[UNI-FI] Usuário {instance.username} cadastrado com sucesso no UniFi")
            else:
                UnifiUserStatus.objects.create(user=instance, cadastrado_unifi=False)
                print(f"[UNI-FI] Falha ao cadastrar usuário {instance.username}")
        except Exception as e:
            print(f"[ERRO UNI-FI] {e}")
            UnifiUserStatus.objects.create(user=instance, cadastrado_unifi=False)
