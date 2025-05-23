from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import UniFiUser, Dispositivo

class DispositivoInline(admin.TabularInline):
    model = Dispositivo
    extra = 1

@admin.register(UniFiUser)
class UniFiUserAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "departamento", "vinculo", "get_mac_addresses", "created_at")
    search_fields = ("nome", "matricula", "dispositivos__mac_address")
    list_filter = ("departamento", "vinculo", "created_at")
    inlines = [DispositivoInline]

    def get_mac_addresses(self, obj):
        return ", ".join([d.mac_address for d in obj.dispositivos.all()])
    get_mac_addresses.short_description = "MAC Addresses"

