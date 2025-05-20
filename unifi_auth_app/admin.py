from django.contrib import admin
from django.contrib import messages
from .unifi_api import UniFiControllerAPI
from django.conf import settings
import urllib3
from .models import UniFiUser, Dispositivo, UnifiUserStatus


# Desabilitar avisos de SSL para certificados auto-assinados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UniFiAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = settings.UNIFI_BASE_URL
        self.username = settings.UNIFI_USERNAME
        self.password = settings.UNIFI_PASSWORD
        self.verify_ssl = False
    
    def __enter__(self):
        self.login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
    
    def login(self):
        login_url = f"{self.base_url}/api/login"
        self.session.post(
            login_url,
            json={
                "username": self.username,
                "password": self.password
            },
            verify=self.verify_ssl
        )
    
    def logout(self):
        try:
            logout_url = f"{self.base_url}/api/logout"
            self.session.get(logout_url, verify=self.verify_ssl)
        except:
            pass
    
    def authorize_guest(self, mac_address):
        auth_url = f"{self.base_url}/api/s/default/cmd/stamgr"
        self.session.post(
            auth_url,
            json={
                "cmd": "authorize-guest",
                "mac": mac_address
            },
            verify=self.verify_ssl
        )
    
    def unauthorize_guest(self, mac_address):
        auth_url = f"{self.base_url}/api/s/default/cmd/stamgr"
        self.session.post(
            auth_url,
            json={
                "cmd": "unauthorize-sta",
                "mac": mac_address
            },
            verify=self.verify_ssl
        )

class DispositivoInline(admin.TabularInline):
    model = Dispositivo
    extra = 1

@admin.register(UniFiUser)
class UniFiUserAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'get_departamento_full', 'get_dispositivos', 'created_at')
    search_fields = ('nome', 'matricula', 'departamento', 'dispositivos__mac_address')
    inlines = [DispositivoInline]

    def get_departamento_full(self, obj):
        return obj.get_departamento_display_full()
    get_departamento_full.short_description = 'Departamento'

    def get_dispositivos(self, obj):
        return ', '.join([f"{d.nome_dispositivo} ({d.mac_address})" for d in obj.dispositivos.all()])
    get_dispositivos.short_description = 'Dispositivos'

    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('nome_dispositivo', 'mac_address', 'usuario', 'created_at')
    search_fields = ('nome_dispositivo', 'mac_address', 'usuario__nome')
    list_filter = ('usuario__departamento',)
    readonly_fields = ('created_at',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Atualiza o widget do campo mac_address para mostrar o valor formatado
        if obj and obj.mac_address:
            form.base_fields['mac_address'].initial = obj.mac_address
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            with UniFiControllerAPI() as unifi:
                unifi.authorize_guest(obj.mac_address)
            messages.success(request, f'Dispositivo {obj.nome_dispositivo} autorizado com sucesso no UniFi Controller!')
        except Exception as e:
            messages.error(request, f'Erro ao autorizar dispositivo no UniFi Controller: {str(e)}')

    def delete_model(self, request, obj):
        try:
            with UniFiControllerAPI() as unifi:
                unifi.unauthorize_guest(obj.mac_address)
            messages.success(request, f'Dispositivo {obj.nome_dispositivo} desautorizado com sucesso no UniFi Controller!')
        except Exception as e:
            messages.error(request, f'Erro ao desautorizar dispositivo no UniFi Controller: {str(e)}')
        super().delete_model(request, obj)

@admin.register(UnifiUserStatus)
class UnifiUserStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'mac_address', 'cadastrado_unifi', 'data_cadastro')
    list_filter = ('cadastrado_unifi',)
    search_fields = ('user__username', 'mac_address')
