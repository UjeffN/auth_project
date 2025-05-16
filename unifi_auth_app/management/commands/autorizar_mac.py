from django.core.management.base import BaseCommand
from unifi_auth_app.models import Dispositivo
from unifi_auth_app.unifi_api import UniFiControllerAPI

class Command(BaseCommand):
    help = 'Autoriza os dispositivos cadastrados no UniFi Controller'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando autorização dos dispositivos...')

        controller = UniFiControllerAPI()

        dispositivos = Dispositivo.objects.all()
        if not dispositivos:
            self.stdout.write(self.style.WARNING('Nenhum dispositivo encontrado para autorizar.'))
            return

        for disp in dispositivos:
            mac = disp.mac_address
            nome = disp.nome_dispositivo
            self.stdout.write(f'Autorizando dispositivo: {nome} - MAC: {mac}')
            try:
                controller.authorize_guest(mac)
                self.stdout.write(self.style.SUCCESS(f'MAC {mac} autorizado com sucesso!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao autorizar MAC {mac}: {e}'))

        self.stdout.write('Processo de autorização finalizado.')

