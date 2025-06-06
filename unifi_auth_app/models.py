import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


# === Funções auxiliares para validar MAC Address ===
def format_mac_address(value):
    """Converte o MAC address para o formato padrão XX:XX:XX:XX:XX:XX em maiúsculas"""
    clean_mac = ''.join(c for c in value if c.isalnum())

    invalid_chars = set(clean_mac) - set('0123456789ABCDEFabcdef')
    if invalid_chars:
        chars_list = ', '.join(sorted(invalid_chars))
        raise ValidationError(
            f'MAC address contém caracteres inválidos: {chars_list}. '
            'Use apenas números (0-9) e letras de A até F'
        )

    if len(clean_mac) != 12:
        raise ValidationError(
            f'MAC address deve ter 12 caracteres hexadecimais, mas tem {len(clean_mac)}. '
            'Formato esperado: XX:XX:XX:XX:XX:XX'
        )

    return ':'.join(clean_mac[i:i+2].upper() for i in range(0, 12, 2))


def validate_mac_address(value):
    return format_mac_address(value)


# === Modelo de Departamento com ordenação personalizada ===
class Departamento(models.TextChoices):
    PRL = 'PRL', _('Presidência Legislativa')
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
    GAB1 = 'GAB1', _('TITO MST')
    GAB2 = 'GAB2', _('MAQUIVALDA')
    GAB3 = 'GAB3', _('ELEOMÁRCIO')
    GAB4 = 'GAB4', _('SGT. NOGUEIRA')
    GAB5 = 'GAB5', _('SADISVAN')
    GAB6 = 'GAB6', _('FRANCISCO ELOÉCIO')
    GAB7 = 'GAB7', _('ZÉ DA LATA')
    GAB8 = 'GAB8', _('ALEX OHANA')
    GAB9 = 'GAB9', _('FRED SANSÃO')
    GAB10 = 'GAB10', _('ZÉ DO BODE')
    GAB11 = 'GAB11', _('LEANDRO CHIQUITO')
    GAB12 = 'GAB12', _('LAÉCIO DA ACT')
    GAB13 = 'GAB13', _('GRACIELE BRITO')
    GAB14 = 'GAB14', _('MICHEL CARTEIRO')
    GAB15 = 'GAB15', _('ELIAS DA CONSTRUFORTE')
    GAB16 = 'GAB16', _('ANDERSON MORATÓRIO')
    GAB17 = 'GAB17', _('ÉRICA RIBEIRO')

    @classmethod
    def ordered_choices(cls):
        return sorted(cls.choices, key=lambda choice: choice[1])


# === Modelo do Usuário ===
class UniFiUser(models.Model):
    nome = models.CharField('Nome', max_length=100)

    matricula = models.CharField(
        'Matrícula',
        max_length=20,
        blank=True,
        null=True,
        unique=False  # Pode mudar depois com regra de negócio
    )

    departamento = models.CharField(
        'Departamento',
        max_length=15,
        choices=Departamento.ordered_choices(),
        default=None
    )

    VINCULO_CHOICES = [
        ('efetivo', 'Efetivo'),
        ('comissionado', 'Comissionado'),
    ]
    vinculo = models.CharField(
        'Vínculo',
        max_length=15,
        choices=VINCULO_CHOICES,
        default='efetivo'
    )

    created_at = models.DateTimeField('Data de Criação', auto_now_add=True)

    class Meta:
        verbose_name = 'Usuário UniFi'
        verbose_name_plural = 'Usuários UniFi'
        ordering = ['nome']

    def get_departamento_display_full(self):
        return f"{self.departamento} - {self.get_departamento_display()}"
    
    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.matricula}"


# === Modelo de Dispositivo ===
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


# === Modelo auxiliar: Status no UniFi Controller ===
class UnifiUserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mac_address = models.CharField(max_length=17, unique=True)  # formato: AA:BB:CC:DD:EE:FF
