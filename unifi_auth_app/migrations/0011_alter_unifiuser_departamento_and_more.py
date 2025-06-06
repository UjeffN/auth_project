# Generated by Django 5.2.1 on 2025-05-20 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unifi_auth_app', '0010_unifiuser_vinculo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unifiuser',
            name='departamento',
            field=models.CharField(choices=[('GAB8', 'ALÉX OHANA'), ('GAB16', 'ANDERSON MORATÓRIO'), ('ARQ', 'Arquivo e Registro'), ('ASC', 'Assessoria de Comunicação'), ('AUT', 'Automação'), ('CER', 'Cerimonial'), ('COM', 'Compras'), ('CONT', 'Contabilidade'), ('CNT', 'Controladoria Interna'), ('DTI', 'Departamento de Tecnologia da Informação'), ('DIA', 'Diretoria Administrativa'), ('DIF', 'Diretoria Financeira'), ('DIL', 'Diretoria Legislativa'), ('GAB3', 'ELEOMÁRCIO'), ('GAB15', 'ELIAS DA CONSTRUFORTE'), ('GAB6', 'FRANCISCO ELOÉCIO'), ('GAB9', 'FRED SANSÃO'), ('GAB13', 'GRACIELE BRITO'), ('ILCM', 'Instituto Legislativo'), ('GAB12', 'LAÉCIO DA ACT'), ('GAB11', 'LEANDRO CHIQUITO'), ('LIC', 'Licitações e Contratos'), ('GAB2', 'MAQUIVALDA'), ('GAB14', 'MICHEL CARTEIRO'), ('MTS', 'Materiais e Serviços'), ('MBL', 'Memorial e Biblioteca Legislativa'), ('OUV', 'Ouvidoria'), ('PAT', 'Patrimônio'), ('PLN', 'Planejamento de Contratações'), ('POL', 'Polícia Legislativa'), ('PRL', 'Presidência Legislativa'), ('PRO', 'Procuradoria'), ('RH', 'Recursos Humanos'), ('RTV', 'Rádio e TV'), ('GAB5', 'SADISVAN'), ('GAB4', 'SGT. NOGUEIRA'), ('SIC', 'Serviço de Informação ao Cidadão'), ('GAB1', 'TITO MST'), ('GAB7', 'ZÉ DA LATA'), ('GAB10', 'ZÉ DO BODE'), ('GAB17', 'ÉRICA RIBEIRO')], default=None, max_length=15, verbose_name='Departamento'),
        ),
        migrations.AlterField(
            model_name='unifiuser',
            name='matricula',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Matrícula'),
        ),
    ]
