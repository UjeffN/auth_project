# Changelog

## [1.1.0] - 2025-05-29
### Melhorias de Performance
- Implementado cache de SSIDs na API UniFi para reduzir requisições (5 minutos de cache)
- Adicionadas operações em lote para gerenciar múltiplos MACs simultaneamente
- Novo signal handler para processar alterações M2M em lote
- Substituição de prints por logging estruturado
- Refatoração da UniFiControllerAPI para melhor organização e tipagem

### Adicionado
- Implementado monitoramento usando django-prometheus
- Endpoint `/metrics` protegido por autenticação de superusuário
- Métricas para:
  - Latência das chamadas à API
  - Contagem total de MACs
  - Operações em lote
  - Cache hits/misses

### Detalhes Técnicos
- Cache implementado na classe UniFiControllerAPI
- Novos métodos bulk_add_macs_to_ssid_whitelist e bulk_remove_macs_from_ssid_whitelist
- Uso de sets para operações eficientes com MACs
- Logging com níveis apropriados (info, warning, error)
- Função centralizada get_unifi_api para configuração da API

## [1.0.0] - Data inicial do projeto
- Implementação inicial do sistema de autenticação UniFi
- Integração com Django Admin
- Sistema básico de gerenciamento de usuários e dispositivos
- Integração com API do UniFi Controller
