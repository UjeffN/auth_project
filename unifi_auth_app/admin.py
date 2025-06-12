from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import UniFiUser, Dispositivo, Visitante, VisitanteDispositivo

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

# Inline para exibir os dispositivos do visitante
class VisitanteDispositivoInline(admin.TabularInline):
    model = VisitanteDispositivo
    extra = 0
    readonly_fields = ('visitante_mac_address', 'visitante_nome_dispositivo', 'visitante_data_cadastro', 'visitante_ultimo_acesso', 'visitante_dispositivo_ativo')
    can_delete = False
    max_num = 0
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(VisitanteDispositivo)
class VisitanteDispositivoAdmin(admin.ModelAdmin):
    list_display = ('visitante', 'format_mac_address', 'visitante_nome_dispositivo', 'status_badge', 'visitante_data_cadastro', 'visitante_ultimo_acesso', 'acoes')
    list_filter = ('visitante_dispositivo_ativo', 'visitante_data_cadastro')
    search_fields = ('visitante__nome', 'visitante__email', 'visitante_mac_address', 'visitante_nome_dispositivo')
    list_select_related = ('visitante',)
    readonly_fields = ('visitante_data_cadastro', 'visitante_ultimo_acesso')
    date_hierarchy = 'visitante_data_cadastro'
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('visitante', 'visitante_mac_address', 'visitante_nome_dispositivo', 'visitante_dispositivo_ativo')
        }),
        ('Informações de Auditoria', {
            'classes': ('collapse',),
            'fields': ('visitante_data_cadastro', 'visitante_ultimo_acesso'),
        }),
    )
    
    def format_mac_address(self, obj):
        return format_html('<span class="mac-address">{}</span>', obj.visitante_mac_address)
    format_mac_address.short_description = 'Endereço MAC'
    format_mac_address.admin_order_field = 'visitante_mac_address'
    
    def status_badge(self, obj):
        if obj.visitante_dispositivo_ativo:
            return format_html('<span class="badge bg-success">Ativo</span>')
        return format_html('<span class="badge bg-secondary">Inativo</span>')
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'visitante_dispositivo_ativo'
    
    def acoes(self, obj):
        return format_html(
            '<a href="{}" class="button" title="Ver detalhes"><i class="fa fa-eye"></i></a> ',
            reverse('admin:unifi_auth_app_visitantedispositivo_change', args=[obj.id])
        )
    acoes.short_description = 'Ações'
    acoes.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        # Verifica se o visitante já tem 3 dispositivos ativos
        if obj.visitante_dispositivo_ativo and obj.visitante.visitante_dispositivos.filter(
            visitante_dispositivo_ativo=True
        ).exclude(pk=obj.pk).count() >= 3:
            messages.set_level(request, messages.ERROR)
            messages.error(
                request,
                'Não é possível ativar este dispositivo. O visitante já possui o número máximo de 3 dispositivos ativos.'
            )
            return
        super().save_model(request, obj, form, change)

# Registra o modelo Visitante
@admin.register(Visitante)
class VisitanteAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "telefone", "get_mac_addresses", "ip_address", "data_acesso", "autorizado", "total_dispositivos_ativos")
    search_fields = ("nome", "email", "telefone", "ip_address", "visitante_dispositivos__visitante_mac_address")
    list_filter = ("autorizado", "data_acesso")
    readonly_fields = ("data_acesso", "total_dispositivos_ativos_display")
    list_editable = ("autorizado",)
    date_hierarchy = 'data_acesso'
    ordering = ('-data_acesso',)
    inlines = [VisitanteDispositivoInline]
    
    def get_mac_addresses(self, obj):
        """Exibe os endereços MAC dos dispositivos do visitante"""
        dispositivos = obj.visitante_dispositivos.all()
        if not dispositivos.exists():
            return "Nenhum dispositivo"
            
        macs = []
        for disp in dispositivos:
            status_icon = "✅" if disp.visitante_dispositivo_ativo else "❌"
            macs.append(f"{disp.visitante_mac_address} {status_icon}")
        return format_html("<br>".join(macs))
    get_mac_addresses.short_description = "Dispositivos (MAC - Status)"
    get_mac_addresses.allow_tags = True
    
    def total_dispositivos_ativos(self, obj):
        """Exibe o total de dispositivos ativos do visitante"""
        total = obj.visitante_dispositivos.filter(visitante_dispositivo_ativo=True).count()
        return format_html('<span class="badge bg-{}">{}/3</span>', 
                         'success' if total <= 3 else 'danger', total)
    total_dispositivos_ativos.short_description = 'Dispositivos Ativos'
    total_dispositivos_ativos.admin_order_field = 'total_dispositivos_ativos'
    
    def total_dispositivos_ativos_display(self, obj):
        """Versão para o formulário de edição"""
        return self.total_dispositivos_ativos(obj)
    total_dispositivos_ativos_display.short_description = 'Total de Dispositivos Ativos'
    
    def get_queryset(self, request):
        """Otimiza a consulta para incluir a contagem de dispositivos ativos"""
        from django.db.models import Count, Case, When, IntegerField
        return super().get_queryset(request).annotate(
            total_dispositivos_ativos=Count(
                Case(
                    When(visitante_dispositivos__visitante_dispositivo_ativo=True, then=1),
                    output_field=IntegerField(),
                )
            )
        )
    
    def response_change(self, request, obj):
        """Redireciona de volta para a lista após salvar"""
        if "_continue" not in request.POST and "_addanother" not in request.POST:
            return HttpResponseRedirect(reverse('admin:unifi_auth_app_visitante_changelist'))
        return super().response_change(request, obj)

    # Adiciona os campos de total de dispositivos à listagem
    def get_list_display(self, request):
        return super().get_list_display(request) + ('total_dispositivos_ativos',)
