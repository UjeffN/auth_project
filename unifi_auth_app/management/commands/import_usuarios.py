import os
import xlrd
from django.core.management.base import BaseCommand
from unifi_auth_app.models import UniFiUser, Departamento

# Dicionário completo de mapeamento de departamentos
DEPARTAMENTO_MAP = {
    'ASSESSORIA DE COMUNICACAO': 'ASC',
    'BIBLIOTECA LEGISLATIVA': 'MBL',
    'CONTABILIDADE': 'CONT',
    'CONTROLADORIA INTERNA': 'CNT',
    'DEPART. DE POLICIA LEGISLATIVA': 'POL',
    'DEPARTAMENTO DE COMPRAS': 'COM',
    'DEPARTAMENTO DE MATERIAIS E SERVICOS': 'MTS',
    'DEPARTAMENTO DE PLANEJAMENTO DE CONTRATACOES': 'PLN',
    'DEPARTAMENTO DE RADIO E TV': 'RTV',
    'DEPARTAMENTO DE TI': 'DTI',
    'DIRETORIA ADMINISTRATIVA': 'DIA',
    'DIRETORIA FINANCEIRA': 'DIF',
    'DIRETORIA LEGISLATIVA': 'DIL',
    'ESCOLA DO LEGISLATIVO': 'ILCM',
    'ILCM - INSTITUTO LEGISLATIVO DA CAMARA MUNICIPAL DE PARAUAPE': 'ILCM',
    'LICITACAO': 'LIC',
    'PATRIMONIO': 'PAT',
    'PRESIDENCIA': 'PRL',
    'PROCURADORIA': 'PRO',
    'RECURSOS HUMANOS': 'RH',
    'SIC-SERVICO DE INFORMACAO AO CIDADAO': 'SIC',

    'GAB. VER. ALEX OHANA': 'GAB8',
    'GAB. VER. ANDERSON MARCOS MORATORIO': 'GAB16',
    'GAB. VER. ELIAS FERREIRA DE ALMEIDA FILHO': 'GAB15',
    'GAB. VER. ELVIS SILVA CRUZ': 'GAB10',
    'GAB. VER. ERICA RIBEIRO': 'GAB17',
    'GAB. VER. FRED SANCAO': 'GAB9',
    'GAB. VER. FRANCISCO ELOECIO SILVA LIMA': 'GAB6',
    'GAB. VER. GRACIELE BRITO': 'GAB13',
    'GAB. VER. LAECIO DA ACT': 'GAB12',
    'GAB. VER. LEONARDO DA SILVA MENDES': 'GAB11',
    'GAB. VER. MAQUIVALDA': 'GAB2',
    'GAB. VER. MICHEL CARTEIRO': 'GAB14',
    'GAB. VER. SADISVAN': 'GAB5',
    'GAB. VER. SARGENTO NOGUEIRA': 'GAB4',
    'GAB. VER. TITO DO MST': 'GAB1',
    'GAB. VER. ZE DA LATA': 'GAB7',
    'GAB. VER. ELEOMARCIO ALMEIDA DE LIMA': 'GAB3'
}


class Command(BaseCommand):
    help = 'Importa usuários do arquivo usuarios.xls'

    def handle(self, *args, **kwargs):
        caminho_arquivo = '/opt/auth_project/imports/usuarios.xls'

        if not os.path.exists(caminho_arquivo):
            self.stderr.write(self.style.ERROR(f"Arquivo não encontrado: {caminho_arquivo}"))
            return

        planilha = xlrd.open_workbook(caminho_arquivo)
        pagina = planilha.sheet_by_index(0)

        criados = 0
        atualizados = 0
        ignorados = 0

        for row_idx in range(1, pagina.nrows):  # Ignora cabeçalho
            linha = pagina.row_values(row_idx)

            # Ordem correta das colunas: MATRICULA, NOME, SETOR_NOME, VINCULO_NOME
            matricula = str(linha[0]).strip()
            nome = str(linha[1]).strip().upper()
            departamento_raw = str(linha[2]).strip().upper()
            vinculo_raw = str(linha[3]).strip().upper()

            # Normaliza o vínculo
            if vinculo_raw in ['COMISSIONADOS', 'VEREADOR']:
                vinculo = 'comissionado'
            elif vinculo_raw == 'EFETIVOS':
                vinculo = 'efetivo'
            else:
                self.stdout.write(self.style.WARNING(
                    f"Vínculo inválido: '{vinculo_raw}' para o usuário '{nome}'"
                ))
                ignorados += 1
                continue

            # Tenta encontrar o departamento no mapeamento
            departamento = DEPARTAMENTO_MAP.get(departamento_raw)

            # Se não encontrou no mapeamento, verifica se já é uma sigla válida
            if not departamento and departamento_raw in [choice[0] for choice in Departamento.choices]:
                departamento = departamento_raw

            if not departamento:
                self.stdout.write(self.style.WARNING(
                    f"Departamento não mapeado: '{departamento_raw}' para o usuário '{nome}'"
                ))
                ignorados += 1
                continue

            # Atualiza ou cria o usuário
            try:
                user, created = UniFiUser.objects.update_or_create(
                    matricula=matricula,
                    defaults={
                        'nome': nome,
                        'vinculo': vinculo,
                        'departamento': departamento
                    }
                )

                if created:
                    criados += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Criado: {nome} ({matricula}) - {departamento}"
                    ))
                else:
                    atualizados += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Atualizado: {nome} ({matricula}) - {departamento}"
                    ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Erro ao processar usuário {nome} ({matricula}): {str(e)}"
                ))
                ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImportação concluída:\n" \
            f"Criados: {criados}\n" \
            f"Atualizados: {atualizados}\n" \
            f"Ignorados: {ignorados}"
        ))
