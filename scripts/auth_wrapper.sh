#!/bin/bash

# Executa o script Python com o Python da virtualenv
output=$(/opt/auth_project/venv/bin/python3 /opt/auth_project/scripts/radius_mac_auth.py "$1")
status=$?

# Formata a resposta para o FreeRADIUS
echo "Reply-Message = \"$output\""
exit $status
