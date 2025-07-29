#!/bin/bash

# Diretórios e arquivos
PROJECT_DIR="/opt/auth_project"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/backup.log"

# Cria os diretórios se não existirem
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Carrega as variáveis de ambiente do arquivo .env
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
else
    echo "$(date) - ERRO: Arquivo .env não encontrado." >> "$LOG_FILE"
    exit 1
fi

# Nome do arquivo de backup com data e hora
BACKUP_FILE="$BACKUP_DIR/unifi_auth_db_backup_$(date +%Y-%m-%d_%H-%M-%S).sql"

# Executa o backup
/usr/bin/mysqldump -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"

# Verifica se o backup foi bem-sucedido e o comprime
if [ $? -eq 0 ]; then
    echo "$(date) - Backup criado com sucesso: $BACKUP_FILE" >> "$LOG_FILE"
    gzip "$BACKUP_FILE"
    echo "$(date) - Backup comprimido: $BACKUP_FILE.gz" >> "$LOG_FILE"
else
    echo "$(date) - ERRO ao criar o backup." >> "$LOG_FILE"
    exit 1
fi

# Remove backups com mais de 7 dias
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +7 -exec rm {} \;
echo "$(date) - Backups com mais de 7 dias foram removidos." >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
