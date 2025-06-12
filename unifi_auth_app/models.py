import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

# Não importamos o User aqui para evitar importação circular
# A importação será feita dentro dos métodos que precisam dele


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
    # Departamentos administrativos
    PRL = 'PRL', 'Presidência Legislativa'
    CER = 'CER', 'Cerimonial'
    ASC = 'ASC', 'Assessoria de Comunicação'
    PRO = 'PRO', 'Procuradoria'
    CNT = 'CNT', 'Controladoria Interna'
    DIF = 'DIF', 'Diretoria Financeira'
    DIL = 'DIL', 'Diretoria Legislativa'
    DIA = 'DIA', 'Diretoria Administrativa'
    OUV = 'OUV', 'Ouvidoria'
    ILCM = 'ILCM', 'Instituto Legislativo'
    ARQ = 'ARQ', 'Arquivo e Registro'
    CONT = 'CONT', 'Contabilidade'
    PAT = 'PAT', 'Patrimônio'
    AUT = 'AUT', 'Automação'
    MBL = 'MBL', 'Memorial e Biblioteca Legislativa'
    RTV = 'RTV', 'Rádio e TV'
    PLN = 'PLN', 'Planejamento de Contratações'
    SIC = 'SIC', 'Serviço de Informação ao Cidadão'
    LIC = 'LIC', 'Licitações e Contratos'
    POL = 'POL', 'Polícia Legislativa'
    RH = 'RH', 'Recursos Humanos'
    MTS = 'MTS', 'Materiais e Serviços'
    COM = 'COM', 'Compras'
    DTI = 'DTI', 'Departamento de Tecnologia da Informação'
    
    # Gabinetes dos deputados
    GAB1 = 'GAB1', 'TITO MST'
    GAB2 = 'GAB2', 'MAQUIVALDA'
    GAB3 = 'GAB3', 'ELEOMÁRCIO'
    GAB4 = 'GAB4', 'SGT. NOGUEIRA'
    GAB5 = 'GAB5', 'SADISVAN'
    GAB6 = 'GAB6', 'FRANCISCO ELOÉCIO'
    GAB7 = 'GAB7', 'ZÉ DA LATA'
    GAB8 = 'GAB8', 'ALEX OHANA'
    GAB9 = 'GAB9', 'FRED SANSÃO'
    GAB10 = 'GAB10', 'ZÉ DO BODE'
    GAB11 = 'GAB11', 'LEANDRO CHIQUITO'
    GAB12 = 'GAB12', 'LAÉCIO DA ACT'
    GAB13 = 'GAB13', 'GRACIELE BRITO'
    GAB14 = 'GAB14', 'MICHEL CARTEIRO'
    GAB15 = 'GAB15', 'ELIAS DA CONSTRUFORTE'
    GAB16 = 'GAB16', 'ANDERSON MORATÓRIO'
    GAB17 = 'GAB17', 'ÉRICA RIBEIRO'
    
    @classmethod
    def ordered_choices(cls):
        """Retorna as escolhas ordenadas pelo nome de exibição"""
        # Ordena as escolhas pelo label sem tradução durante o carregamento
        return sorted(cls.choices, key=lambda x: x[1])
    
    @classmethod
    def get_translated_choices(cls):
        """Retorna as escolhas traduzidas (para uso em views e templates)"""
        from django.utils.translation import gettext_lazy as _
        return [(value, _(label)) for value, label in cls.choices]


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


# Importação movida para user_status.py para evitar importação circular
# Consulte user_status.py para a definição de UnifiUserStatus  # formato: AA:BB:CC:DD:EE:FF


class Visitante(models.Model):
    """Modelo para armazenar informações dos visitantes da rede"""
    nome = models.CharField('Nome Completo', max_length=200)
    email = models.EmailField('E-mail')
    telefone = models.CharField('Telefone', max_length=20)
    mac_address = models.CharField('Endereço MAC', max_length=17)
    data_acesso = models.DateTimeField('Data e Hora do Acesso', auto_now_add=True)
    ip_address = models.GenericIPAddressField('Endereço IP', null=True, blank=True)
    autorizado = models.BooleanField('Autorizado', default=False)
    
    class Meta:
        verbose_name = 'Visitante'
        verbose_name_plural = 'Visitantes'
        ordering = ['-data_acesso']
    
    def __str__(self):
        return f"{self.nome} - {self.email} ({self.data_acesso.strftime('%d/%m/%Y %H:%M')})"
