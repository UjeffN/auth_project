from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import UniFiUser, Visitante, VisitanteDispositivo
from .validators import validate_visitante_mac_address

class UniFiUserForm(forms.ModelForm):
    class Meta:
        model = UniFiUser
        fields = ['nome', 'matricula', 'departamento', 'vinculo']

class VisitanteForm(forms.ModelForm):
    telefone = forms.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{10,11}$', 'Digite um telefone válido')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000000'})
    )
    aceite_lgpd = forms.BooleanField(
        required=True,
        label='Li e concordo com os termos da Lei Geral de Proteção de Dados (LGPD)'
    )
    aceite_politica = forms.BooleanField(
        required=True,
        label='Li e concordo com a Política de Segurança da Informação'
    )

    class Meta:
        model = Visitante
        fields = ['nome', 'telefone', 'email', 'aceite_lgpd', 'aceite_politica']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
        }

class CodigoValidacaoForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r'^[0-9]{6}$', 'O código deve conter 6 dígitos numéricos')],
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'style': 'letter-spacing: 0.35em; font-size: 24px; font-weight: bold;',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'one-time-code'
        })
    )

class VisitanteDispositivoForm(forms.ModelForm):
    """Formulário para adicionar/editar dispositivos de visitantes"""
    
    class Meta:
        model = VisitanteDispositivo
        fields = [
            'visitante', 
            'visitante_mac_address', 
            'visitante_nome_dispositivo', 
            'visitante_dispositivo_ativo'
        ]
        labels = {
            'visitante': 'Visitante',
            'visitante_mac_address': 'Endereço MAC',
            'visitante_nome_dispositivo': 'Nome do Dispositivo',
            'visitante_dispositivo_ativo': 'Dispositivo Ativo'
        }
        help_texts = {
            'visitante_mac_address': 'Formato: XX:XX:XX:XX:XX:XX ou XX-XX-XX-XX-XX-XX',
            'visitante_nome_dispositivo': 'Nome amigável para identificar o dispositivo',
            'visitante_dispositivo_ativo': 'Desmarque para desativar este dispositivo temporariamente'
        }
        widgets = {
            'visitante': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione um visitante...',
            }),
            'visitante_mac_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00:11:22:33:44:55',
            }),
            'visitante_nome_dispositivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Celular do João',
            }),
            'visitante_dispositivo_ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        # Extrai o parâmetro 'user' se existir
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Se for uma atualização, não permitir alterar o visitante
        if self.instance and self.instance.pk:
            self.fields['visitante'].disabled = True
            self.fields['visitante'].widget.attrs['readonly'] = True
        
        # Se for criação e não tiver usuário, limpa a lista de visitantes
        if not self.instance.pk and not self.user:
            self.fields['visitante'].queryset = Visitante.objects.none()
    
    def clean_visitante_mac_address(self):
        """Valida e formata o endereço MAC"""
        mac_address = self.cleaned_data.get('visitante_mac_address')
        
        if not mac_address:
            return mac_address
        
        try:
            # Usa o validador de MAC para visitantes
            mac_address = validate_visitante_mac_address(mac_address)
            
            # Verifica se já existe um dispositivo ativo com este MAC
            qs = VisitanteDispositivo.objects.filter(
                visitante_mac_address=mac_address,
                visitante_dispositivo_ativo=True
            )
            
            # Se estiver editando, exclui o próprio registro da verificação
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    'Já existe um dispositivo ativo com este endereço MAC.'
                )
                
            return mac_address
            
        except ValidationError as e:
            raise ValidationError(f'Endereço MAC inválido: {e}')
    
    def clean(self):
        cleaned_data = super().clean()
        visitante = cleaned_data.get('visitante')
        ativo = cleaned_data.get('visitante_dispositivo_ativo', False)
        
        # Se for um novo dispositivo ou estiver ativando um existente
        if not self.instance.pk or (self.instance and ativo):
            # Verifica se o visitante já tem 3 dispositivos ativos
            if visitante and visitante.visitante_dispositivos.filter(
                visitante_dispositivo_ativo=True
            ).exclude(pk=self.instance.pk if self.instance else None).count() >= 3:
                raise ValidationError({
                    'visitante': 'Este visitante já possui o número máximo de dispositivos ativos (3).'
                })
        
        return cleaned_data
