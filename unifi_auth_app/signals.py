import os
import logging
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Dispositivo, VisitanteDispositivo, UniFiUser
from django.utils.timezone import now
from django.conf import settings
from django.core.exceptions import ValidationError

# Configuração de logging
logger = logging.getLogger('unifi_auth_app')

# Importa o modelo UnifiUserStatus se existir
try:
    from .user_status import UnifiUserStatus
    UNIFI_USER_STATUS_AVAILABLE = True
except ImportError:
    UNIFI_USER_STATUS_AVAILABLE = False

# Importa a API do UniFi se as configurações estiverem disponíveis
UNIFI_CONFIGURED = all([
    os.getenv('UNIFI_URL'),
    os.getenv('UNIFI_USER'),
    os.getenv('UNIFI_PASSWORD'),
    os.getenv('UNIFI_SITE_ID')
])

if UNIFI_CONFIGURED:
    try:
        from .unifi_api import UniFiControllerAPI
        
        # Nome da rede Wi-Fi para a qual os dispositivos serão adicionados à whitelist
        UNIFI_SSID = os.getenv('UNIFI_SSID')
        
    except ImportError:
        logger.warning("Módulo unifi_api não encontrado. A integração com o UniFi será desativada.")
        UNIFI_CONFIGURED = False

def get_unifi_api():
    """Retorna uma instância da API do UniFi configurada."""
    if not UNIFI_CONFIGURED:
        return None
        
    try:
        return UniFiControllerAPI(
            base_url=os.getenv('UNIFI_URL'),
            site=os.getenv('UNIFI_SITE_ID', 'default'),
            username=os.getenv('UNIFI_USER'),
            password=os.getenv('UNIFI_PASSWORD'),
            verify_ssl=False  # Desativa verificação SSL para desenvolvimento
        )
    except Exception as e:
        logger.error(f"Erro ao inicializar a API do UniFi: {str(e)}")
        return None

def adicionar_mac_a_whitelist(mac_address, ssid=None):
    """
    Adiciona um endereço MAC à whitelist do UniFi.
    
    Args:
        mac_address (str): Endereço MAC a ser adicionado
        ssid (str, optional): Nome da rede Wi-Fi. Se não informado, usa o valor de UNIFI_SSID
    
    Returns:
        bool: True se o MAC foi adicionado com sucesso, False caso contrário
    """
    if not UNIFI_CONFIGURED:
        logger.warning("Integração com UniFi não está configurada. Ignorando adição de MAC à whitelist.")
        return False
    
    if not mac_address:
        logger.error("Nenhum endereço MAC fornecido para adicionar à whitelist.")
        return False
    
    try:
        api = get_unifi_api()
        if not api:
            return False
        
        ssid = ssid or UNIFI_SSID
        logger.info(f"Adicionando MAC {mac_address} à whitelist do SSID: {ssid}")
        
        # Usa o método apropriado da API para adicionar o MAC à whitelist
        result = api.add_mac_to_ssid_whitelist(mac_address, ssid)
        
        if result:
            logger.info(f"MAC {mac_address} adicionado com sucesso à whitelist do SSID {ssid}")
        else:
            logger.warning(f"Falha ao adicionar MAC {mac_address} à whitelist do SSID {ssid}")
        
        return bool(result)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar MAC {mac_address} à whitelist: {str(e)}")
        return False

@receiver(post_save, sender=User)
def cadastrar_no_unifi(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Novo usuário criado: {instance.username}")
        
        # Só tenta criar o usuário no UniFi se a API estiver configurada
        if UNIFI_CONFIGURED and UNIFI_USER_STATUS_AVAILABLE:
            try:
                api = get_unifi_api()
                if not api:
                    return
                
                # Tenta criar o usuário no UniFi
                sucesso = api.criar_usuario(instance.username)
                
                # Se o modelo UnifiUserStatus estiver disponível, cria o registro
                if sucesso and UNIFI_USER_STATUS_AVAILABLE:
                    try:
                        UnifiUserStatus.objects.create(
                            user=instance,
                            mac_address='',  # Preencher com o MAC address se disponível
                            data_cadastro=now()
                        )
                        logger.info(f"[SIGNAL] Usuário {instance.username} cadastrado com sucesso no UniFi")
                    except Exception as e:
                        logger.error(f"Erro ao criar registro UnifiUserStatus para {instance.username}: {str(e)}")
                else:
                    logger.error(f"[SIGNAL] Falha ao cadastrar usuário {instance.username} no UniFi")
                
            except Exception as e:
                logger.error(f"[SIGNAL] Erro ao conectar com a API do UniFi: {str(e)}")
        else:
            logger.info("[SIGNAL] Aviso: Integração com UniFi não configurada ou desativada")
            
            # Se o modelo UnifiUserStatus estiver disponível, cria o registro sem integração com UniFi
            if UNIFI_USER_STATUS_AVAILABLE:
                try:
                    UnifiUserStatus.objects.create(
                        user=instance,
                        mac_address='',
                        data_cadastro=now()
                    )
                except Exception as e:
                    logger.error(f"Erro ao criar registro UnifiUserStatus: {str(e)}")

@receiver(post_save, sender=Dispositivo)
def adicionar_dispositivo_unifi(sender, instance, created, **kwargs):
    """
    Adiciona o endereço MAC de um dispositivo à whitelist do UniFi quando o dispositivo é salvo.
    """
    if created or kwargs.get('update_fields') is None:  # Se for uma criação ou atualização completa
        logger.info(f"Dispositivo salvo: {instance.mac_address} (Usuário: {instance.usuario.nome})")
        
        # Adiciona o MAC à whitelist do UniFi
        adicionar_mac_a_whitelist(instance.mac_address)

@receiver(post_save, sender=VisitanteDispositivo)
def adicionar_visitante_dispositivo_unifi(sender, instance, created, **kwargs):
    """
    Adiciona o endereço MAC de um dispositivo de visitante à whitelist do UniFi quando o dispositivo é salvo.
    """
    if (created or kwargs.get('update_fields') is None) and instance.visitante_dispositivo_ativo:
        logger.info(f"Dispositivo de visitante salvo: {instance.visitante_mac_address} (Visitante: {instance.visitante.nome})")
        
        # Adiciona o MAC à whitelist do UniFi
        adicionar_mac_a_whitelist(instance.visitante_mac_address)

@receiver(pre_delete, sender=VisitanteDispositivo)
def remover_visitante_dispositivo_unifi(sender, instance, **kwargs):
    """
    Remove o endereço MAC de um dispositivo de visitante da whitelist do UniFi quando o dispositivo é excluído.
    """
    if instance.visitante_dispositivo_ativo and instance.visitante_mac_address:
        logger.info(f"Dispositivo de visitante removido: {instance.visitante_mac_address} (Visitante: {instance.visitante.nome})")
        
        try:
            # Usa o SSID específico para visitantes, ou o padrão se não estiver configurado
            ssid_visitantes = getattr(settings, 'UNIFI_SSID_VISITANTES', 'Câmara')
            
            api = get_unifi_api()
            if api:
                resposta = api.remove_mac_from_ssid_whitelist(
                    instance.visitante_mac_address, 
                    ssid_name=ssid_visitantes
                )
                logger.info(f"[UNI-FI] Dispositivo {instance.visitante_mac_address} removido da whitelist do SSID '{ssid_visitantes}': {resposta}")
        except Exception as e:
            logger.error(f"[ERRO UNI-FI] Falha ao remover dispositivo {instance.visitante_mac_address}: {e}")

@receiver(pre_delete, sender=UniFiUser)
def remover_dispositivos_usuario_unifi(sender, instance, **kwargs):
    """
    Remove todos os endereços MAC associados a um usuário da whitelist do UniFi quando o usuário é excluído.
    """
    try:
        # Obtém o SSID da configuração
        ssid = getattr(settings, 'UNIFI_SSID', 'Câmara')
        api = get_unifi_api()
        
        if not api:
            logger.warning("API do UniFi não disponível. Não foi possível remover dispositivos do usuário.")
            return
            
        # Remove cada dispositivo do usuário da whitelist
        for dispositivo in instance.dispositivos.all():
            try:
                logger.info(f"Removendo dispositivo {dispositivo.mac_address} do usuário {instance.nome} da whitelist...")
                resposta = api.remove_mac_from_ssid_whitelist(
                    dispositivo.mac_address,
                    ssid_name=ssid
                )
                logger.info(f"[UNI-FI] Dispositivo {dispositivo.mac_address} removido da whitelist do SSID '{ssid}': {resposta}")
            except Exception as e:
                logger.error(f"[ERRO UNI-FI] Falha ao remover dispositivo {dispositivo.mac_address}: {e}")
                
    except Exception as e:
        logger.error(f"[ERRO UNI-FI] Erro ao processar remoção de dispositivos do usuário {instance.nome}: {e}")
