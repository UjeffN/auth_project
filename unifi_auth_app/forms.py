from django import forms
from .models import UniFiUser

class UniFiUserForm(forms.ModelForm):
    class Meta:
        model = UniFiUser
        fields = ['nome', 'matricula', 'mac_address']
