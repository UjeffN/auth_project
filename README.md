# 📶 API de Autorização Wi-Fi com Django e UniFi

Este projeto é uma aplicação Django projetada para gerenciar a autorização de usuários e dispositivos em uma rede Wi-Fi controlada por um UniFi Controller. Ele fornece um portal cativo para autenticação e um painel administrativo para gerenciamento.

## ✨ Funcionalidades

- Portal cativo para autenticação de usuários na rede Wi-Fi.
- Integração com o UniFi Controller para autorizar e desautorizar dispositivos.
- Painel de administração para gerenciar usuários, dispositivos e permissões.
- Sistema de backup automático para o banco de dados.

---

## 🚀 Guia de Instalação

Siga os passos abaixo para configurar e executar o projeto em um novo ambiente (testado em Ubuntu/Debian).

### 1. Pré-requisitos do Sistema

Primeiro, instale as dependências essenciais do sistema:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv mariadb-server build-essential libmysqlclient-dev
```

### 2. Configuração do Banco de Dados (MariaDB)

Faça login no MariaDB e crie o banco de dados e o usuário para a aplicação.

```bash
sudo mysql -u root -p
```

Dentro do console do MariaDB, execute os seguintes comandos. Substitua `sua_senha_segura` por uma senha forte:

```sql
CREATE DATABASE unifi_auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'unifi_auth_user'@'localhost' IDENTIFIED BY 'sua_senha_segura';
GRANT ALL PRIVILEGES ON unifi_auth_db.* TO 'unifi_auth_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Instalação da Aplicação

Clone o repositório e configure o ambiente virtual do Python.

```bash
# Clone o repositório
git clone https://github.com/UjeffN/auth_project.git
cd auth_project

# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale as dependências do Python
pip install -r requirements.txt
```

### 4. Configuração do Ambiente

Copie o arquivo de exemplo `.env.example` para criar seu próprio arquivo de configuração `.env`.

```bash
cp .env.example .env
```

Agora, edite o arquivo `.env` e preencha as variáveis com suas credenciais. Preste atenção especial às seguintes variáveis:

- `SECRET_KEY`: Gere uma chave secreta forte. Você pode usar um gerador online.
- `DB_NAME`: `unifi_auth_db` (o nome que você criou)
- `DB_USER`: `unifi_auth_user` (o usuário que você criou)
- `DB_PASSWORD`: `sua_senha_segura` (a senha que você definiu)
- `UNIFI_URL`, `UNIFI_USER`, `UNIFI_PASSWORD`: Suas credenciais do UniFi Controller.

### 5. Executando a Aplicação

Com tudo configurado, aplique as migrações do banco de dados, crie um superusuário e inicie o servidor.

```bash
# Aplica as migrações do banco de dados
python manage.py migrate

# Cria um usuário administrador
python manage.py createsuperuser

# Inicia o servidor de desenvolvimento
python manage.py runserver
```

A aplicação estará disponível em `http://127.0.0.1:8000`.

### 6. Deploy com Gunicorn (Produção)

Para um ambiente de produção, é recomendado usar um servidor de aplicação como o Gunicorn.

```bash
gunicorn --workers 3 --bind 0.0.0.0:8000 unifi_auth_project.wsgi:application
```

Considere usar um gerenciador de processos como o `systemd` para manter o Gunicorn rodando em segundo plano. Um exemplo de arquivo de serviço (`gunicorn.service`) está incluído no projeto.

---

## 💾 Backup e Restauração

O projeto está configurado com um script (`scripts/backup.sh`) que realiza backups diários e automáticos do banco de dados via `cron`.

- **Localização**: Os backups são armazenados em `/opt/auth_project/backups/`.
- **Formato**: São arquivos SQL compactados (`.sql.gz`) com a data e hora no nome.
- **Retenção**: Backups com mais de 7 dias são automaticamente excluídos para economizar espaço.

### Como Restaurar um Backup

Siga os passos abaixo para restaurar o banco de dados a partir de um arquivo de backup. **Atenção: este processo substituirá todos os dados atuais do banco de dados.**

1.  **Navegue até o diretório de backups** e liste os arquivos para escolher qual restaurar:

    ```bash
    cd /opt/auth_project/backups/
    ls -l
    ```

2.  **Descompacte o arquivo de backup escolhido**. Substitua `nome_do_arquivo.sql.gz` pelo nome do seu arquivo:

    ```bash
    gunzip nome_do_arquivo.sql.gz
    ```

    Isso criará um arquivo `.sql` descompactado (ex: `unifi_auth_db_2024-07-29_03-00-01.sql`).

3.  **Importe o backup para o MariaDB**. Você precisará das credenciais do banco de dados, que estão no seu arquivo `.env`. O comando abaixo carrega as variáveis do `.env` e executa a importação:

    ```bash
    # Carrega as variáveis de ambiente do .env
    set -a; source /opt/auth_project/.env; set +a

    # Importa o banco de dados (substitua o nome do arquivo)
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < nome_do_arquivo.sql
    ```

4.  **Verifique a restauração**: Acesse a aplicação ou o painel de administração para confirmar que os dados foram restaurados corretamente.

5.  **(Opcional) Limpeza**: Após confirmar que a restauração foi bem-sucedida, você pode apagar o arquivo `.sql` descompactado para economizar espaço:

    ```bash
    rm nome_do_arquivo.sql
    ```
