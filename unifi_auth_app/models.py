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


class VisitanteDispositivo(models.Model):
    """
    Modelo para armazenar os dispositivos associados a um visitante.
    Um visitante pode ter até 3 dispositivos ativos associados.
    """
    visitante = models.ForeignKey(
        'Visitante',
        on_delete=models.CASCADE,
        related_name='visitante_dispositivos',
        verbose_name='Visitante',
        help_text='Visitante ao qual este dispositivo está associado'
    )
    
    visitante_mac_address = models.CharField(
        'Endereço MAC do Dispositivo',
        max_length=17,
        validators=[validate_mac_address],
        help_text='Endereço MAC do dispositivo do visitante. Formato: XX:XX:XX:XX:XX:XX'
    )
    
    visitante_nome_dispositivo = models.CharField(
        'Nome do Dispositivo',
        max_length=100,
        blank=True,
        null=True,
        help_text='Nome amigável para identificar o dispositivo (opcional)'
    )
    
    visitante_data_cadastro = models.DateTimeField(
        'Data de Cadastro',
        auto_now_add=True,
        help_text='Data e hora em que o dispositivo foi cadastrado'
    )
    
    visitante_ultimo_acesso = models.DateTimeField(
        'Último Acesso',
        auto_now=True,
        help_text='Data e hora do último acesso do dispositivo'
    )
    
    visitante_dispositivo_ativo = models.BooleanField(
        'Dispositivo Ativo',
        default=True,
        help_text='Indica se o dispositivo está atualmente autorizado'
    )
    
    class Meta:
        verbose_name = 'Dispositivo de Visitante'
        verbose_name_plural = 'Dispositivos de Visitantes'
        unique_together = ('visitante', 'visitante_mac_address')
        ordering = ['-visitante_ultimo_acesso']
    
    def __str__(self):
        nome = self.visitante_nome_dispositivo or 'Dispositivo sem nome'
        return f"{nome} ({self.visitante_mac_address}) - {self.visitante.nome}"
    
    def clean(self):
        """
        Validações adicionais do modelo.
        """
        # Aplica a formatação do MAC address
        if self.visitante_mac_address:
            self.visitante_mac_address = format_mac_address(self.visitante_mac_address)
        
        # Se for uma atualização e o dispositivo já existir, verifica se está sendo ativado
        if self.pk:
            try:
                old_instance = VisitanteDispositivo.objects.get(pk=self.pk)
                if not old_instance.visitante_dispositivo_ativo and self.visitante_dispositivo_ativo:
                    # Verifica se o visitante já tem 3 dispositivos ativos
                    if self.visitante.visitante_dispositivos.filter(
                        visitante_dispositivo_ativo=True
                    ).exclude(pk=self.pk).count() >= 3:
                        raise ValidationError({
                            'visitante_dispositivo_ativo': 
                                'Este visitante já possui o número máximo de dispositivos ativos (3).'
                        })
            except VisitanteDispositivo.DoesNotExist:
                pass
        
        # Se for um novo registro ou estiver sendo ativado
        if not self.pk or (self.pk and self.visitante_dispositivo_ativo):
            # Verifica se já existe um dispositivo ativo com o mesmo MAC
            if VisitanteDispositivo.objects.filter(
                visitante_mac_address=self.visitante_mac_address,
                visitante_dispositivo_ativo=True
            ).exclude(pk=self.pk if self.pk else None).exists():
                raise ValidationError({
                    'visitante_mac_address': 
                        'Já existe um dispositivo ativo com este endereço MAC.'
                })
            
            # Verifica se o visitante já tem 3 dispositivos ativos
            if (self.visitante and 
                self.visitante.visitante_dispositivos.filter(
                    visitante_dispositivo_ativo=True
                ).exclude(pk=self.pk if self.pk else None).count() >= 3):
                raise ValidationError({
                    'visitante': 
                        'Este visitante já possui o número máximo de dispositivos ativos (3).'
                })
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir validações adicionais.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class Visitante(models.Model):
    """
    Modelo para armazenar informações dos visitantes da rede.
    Um visitante pode ter até 3 dispositivos ativos associados.
    """
    nome = models.CharField(
        'Nome Completo',
        max_length=200,
        help_text='Nome completo do visitante'
    )
    
    email = models.EmailField(
        'E-mail',
        help_text='E-mail para contato do visitante'
    )
    
    telefone = models.CharField(
        'Telefone',
        max_length=20,
        help_text='Telefone para contato do visitante'
    )
    
    data_acesso = models.DateTimeField(
        'Data e Hora do Acesso',
        auto_now_add=True,
        help_text='Data e hora em que o visitante acessou a rede'
    )
    
    ip_address = models.GenericIPAddressField(
        'Endereço IP',
        null=True,
        blank=True,
        help_text='Endereço IP atribuído ao visitante'
    )
    
    autorizado = models.BooleanField(
        'Autorizado',
        default=False,
        help_text='Indica se o visitante está autorizado a acessar a rede'
    )
    
    # Campo mantido para compatibilidade, mas não será mais usado
    mac_address = models.CharField(
        'Endereço MAC (Legado)',
        max_length=17,
        blank=True,
        null=True,
        help_text='Campo mantido para compatibilidade. Use a tabela de dispositivos para novos registros.'
    )
    
    class Meta:
        verbose_name = 'Visitante'
        verbose_name_plural = 'Visitantes'
        ordering = ['-data_acesso']
    
    def __str__(self):
        return f"{self.nome} - {self.email} ({self.data_acesso.strftime('%d/%m/%Y %H:%M')})"
    
    def adicionar_dispositivo(self, mac_address, nome_dispositivo=None):
        """
        Adiciona um novo dispositivo ao visitante.
        
        Args:
            mac_address (str): Endereço MAC do dispositivo
            nome_dispositivo (str, optional): Nome amigável para o dispositivo
            
        Returns:
            VisitanteDispositivo: O dispositivo criado ou atualizado
            
        Raises:
            ValidationError: Se o visitante já tiver 3 dispositivos ativos
        """
        # Verifica se o visitante já tem 3 dispositivos ativos
        if self.visitante_dispositivos.filter(visitante_dispositivo_ativo=True).count() >= 3:
            raise ValidationError('Este visitante já possui o número máximo de dispositivos ativos (3).')
        
        # Tenta encontrar um dispositivo inativo com o mesmo MAC
        dispositivo = self.visitante_dispositivos.filter(
            visitante_mac_address=mac_address
        ).first()
        
        if dispositivo:
            # Se o dispositivo existe e está inativo, reativa-o
            if not dispositivo.visitante_dispositivo_ativo:
                dispositivo.visitante_dispositivo_ativo = True
                if nome_dispositivo:
                    dispositivo.visitante_nome_dispositivo = nome_dispositivo
                dispositivo.save()
                return dispositivo
            else:
                # Dispositivo já existe e está ativo
                return dispositivo
        else:
            # Cria um novo dispositivo
            return self.visitante_dispositivos.create(
                visitante_mac_address=mac_address,
                visitante_nome_dispositivo=nome_dispositivo or f"Dispositivo {self.visitante_dispositivos.count() + 1}"
            )
    
    def remover_dispositivo(self, mac_address):
        """
        Remove um dispositivo do visitante (desativa).
        
        Args:
            mac_address (str): Endereço MAC do dispositivo a ser removido
            
        Returns:
            bool: True se o dispositivo foi removido, False caso contrário
        """
        dispositivo = self.visitante_dispositivos.filter(
            visitante_mac_address=mac_address,
            visitante_dispositivo_ativo=True
        ).first()
        
        if dispositivo:
            dispositivo.visitante_dispositivo_ativo = False
            dispositivo.save()
            return True
        return False
    
    def get_dispositivos_ativos(self):
        """
        Retorna a lista de dispositivos ativos do visitante.
        
        Returns:
            QuerySet: Lista de dispositivos ativos ordenados pelo último acesso
        """
        return self.visitante_dispositivos.filter(
            visitante_dispositivo_ativo=True
        ).order_by('-visitante_ultimo_acesso')
    
    def pode_adicionar_dispositivo(self):
        """
        Verifica se o visitante pode adicionar mais dispositivos.
        
        Returns:
            bool: True se puder adicionar mais dispositivos, False caso contrário
        """
        return self.visitante_dispositivos.filter(
            visitante_dispositivo_ativo=True
        ).count() < 3
