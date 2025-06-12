from django.db import models
from django.contrib.auth import get_user_model

class UnifiUserStatus(models.Model):
    """Modelo para armazenar o status do usuário no UniFi Controller"""
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='unifi_status'
    )
    mac_address = models.CharField(max_length=17, unique=True)
    
    class Meta:
        verbose_name = 'Status do Usuário UniFi'
        verbose_name_plural = 'Status dos Usuários UniFi'
    
    def __str__(self):
        return f"{self.user.username} - {self.mac_address}"
