from django import forms
from django.core.validators import RegexValidator
from .models import UniFiUser, Visitante

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
