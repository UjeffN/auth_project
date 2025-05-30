# Generated by Django 5.2.1 on 2025-05-19 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unifi_auth_app', '0008_unifiuserstatus_mac_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unifiuser',
            name='departamento',
            field=models.CharField(choices=[('PRL', 'Presidência Legislativa'), ('CER', 'Cerimonial'), ('ASC', 'Assessoria de Comunicação'), ('PRO', 'Procuradoria'), ('CNT', 'Controladoria Interna'), ('DIF', 'Diretoria Financeira'), ('DIL', 'Diretoria Legislativa'), ('DIA', 'Diretoria Administrativa'), ('OUV', 'Ouvidoria'), ('ILCM', 'Instituto Legislativo'), ('ARQ', 'Arquivo e Registro'), ('CONT', 'Contabilidade'), ('PAT', 'Patrimônio'), ('AUT', 'Automação'), ('MBL', 'Memorial e Biblioteca Legislativa'), ('RTV', 'Rádio e TV'), ('PLN', 'Planejamento de Contratações'), ('SIC', 'Serviço de Informação ao Cidadão'), ('LIC', 'Licitações e Contratos'), ('POL', 'Polícia Legislativa'), ('RH', 'Recursos Humanos'), ('MTS', 'Materiais e Serviços'), ('COM', 'Compras'), ('DTI', 'Departamento de Tecnologia da Informação'), ('GAB1', 'TITO MST'), ('GAB2', 'MAQUIVALDA'), ('GAB3', 'ELEOMÁRCIO'), ('GAB4', 'SGT. NOGUEIRA'), ('GAB5', 'SADISVAN'), ('GAB6', 'FRANCISCO ELOÉCIO'), ('GAB7', 'ZÉ DA LATA'), ('GAB8', 'ALÉX OHANA'), ('GAB9', 'FRED SANSÃO'), ('GAB10', 'ZÉ DO BODE'), ('GAB11', 'LEANDRO CHIQUITO'), ('GAB12', 'LAÉCIO DA ACT'), ('GAB13', 'GRACIELE BRITO'), ('GAB14', 'MICHEL CARTEIRO'), ('GAB15', 'ELIAS DA CONSTRUFORTE'), ('GAB16', 'ANDERSON MORATÓRIO'), ('GAB17', 'ÉRICA RIBEIRO')], default=None, max_length=15, verbose_name='Departamento'),
        ),
    ]
