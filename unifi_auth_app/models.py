from django.db import models
from django.core.exceptions import ValidationError
import re
from django.utils.translation import gettext_lazy as _

def format_mac_address(value):
    """Converte o MAC address para o formato padrão XX:XX:XX:XX:XX:XX em maiúsculas"""
    # Remove todos os separadores
    clean_mac = ''.join(c for c in value if c.isalnum())
    
    # Encontra caracteres inválidos
    invalid_chars = set(clean_mac) - set('0123456789ABCDEFabcdef')
    if invalid_chars:
        chars_list = ', '.join(sorted(invalid_chars))
        raise ValidationError(
            f'MAC address contém caracteres inválidos: {chars_list}. '
            'Use apenas números (0-9) e letras de A até F'
        )
    
    # Verifica se tem 12 caracteres (6 bytes)
    if len(clean_mac) != 12:
        raise ValidationError(
            f'MAC address deve ter 12 caracteres hexadecimais, mas tem {len(clean_mac)}. '
            'Formato esperado: XX:XX:XX:XX:XX:XX'
        )
    
    # Converte para maiúsculas e insere os dois pontos
    return ':'.join(clean_mac[i:i+2].upper() for i in range(0, 12, 2))

def validate_mac_address(value):
    return format_mac_address(value)

class Dispositivo(models.Model):
    usuario = models.ForeignKey('UniFiUser', on_delete=models.CASCADE, related_name='dispositivos')
    mac_address = models.CharField(
        'MAC Address',
        max_length=17,
        unique=True,
        validators=[validate_mac_address],
        help_text='Formato: XX:XX:XX:XX:XX:XX ou XX-XX-XX-XX-XX-XX (pode usar maiúsculas ou minúsculas)'
    )
    nome_dispositivo = models.CharField('Nome do Dispositivo', max_length=100)
    created_at = models.DateTimeField('Data de Criação', auto_now_add=True)

    def clean(self):
        # Padroniza o formato do MAC address antes da validação
        if self.mac_address:
            self.mac_address = format_mac_address(self.mac_address)
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        ordering = ['usuario__nome', 'nome_dispositivo']

    def __str__(self):
        return f"{self.nome_dispositivo} - {self.mac_address} ({self.usuario.nome})"

class Departamento(models.TextChoices):
    CER = 'CER', _('Cerimonial')
    ASC = 'ASC', _('Assessoria de Comunicação')
    PRO = 'PRO', _('Procuradoria')
    CNT = 'CNT', _('Controladoria Interna')
    DIF = 'DIF', _('Diretoria Financeira')
    DIL = 'DIL', _('Diretoria Legislativa')
    DIA = 'DIA', _('Diretoria Administrativa')
    OUV = 'OUV', _('Ouvidoria')
    ILCM = 'ILCM', _('Instituto Legislativo')
    ARQ = 'ARQ', _('Arquivo e Registro')
    CONT = 'CONT', _('Contabilidade')
    PAT = 'PAT', _('Patrimônio')
    AUT = 'AUT', _('Automação')
    MBL = 'MBL', _('Memorial e Biblioteca Legislativa')
    RTV = 'RTV', _('Rádio e TV')
    PLN = 'PLN', _('Planejamento de Contratações')
    SIC = 'SIC', _('Serviço de Informação ao Cidadão')
    LIC = 'LIC', _('Licitações e Contratos')
    POL = 'POL', _('Polícia Legislativa')
    RH = 'RH', _('Recursos Humanos')
    MTS = 'MTS', _('Materiais e Serviços')
    COM = 'COM', _('Compras')
    DTI = 'DTI', _('Departamento de Tecnologia da Informação')

class UniFiUser(models.Model):
    nome = models.CharField('Nome', max_length=100)
    matricula = models.CharField('Matrícula', max_length=20, unique=True)
    departamento = models.CharField(
        'Departamento',
        max_length=4,
        choices=Departamento.choices,
        default=Departamento.DTI
    )
    created_at = models.DateTimeField('Data de Criação', auto_now_add=True)

    class Meta:
        verbose_name = 'Usuário UniFi'
        verbose_name_plural = 'Usuários UniFi'
        ordering = ['nome']

    def get_departamento_display_full(self):
        return f"{self.departamento} - {self.get_departamento_display()}"

    def __str__(self):
        return f"{self.nome} - {self.matricula}"
