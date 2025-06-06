# Métricas da API UniFi

Este documento descreve as métricas disponíveis para monitoramento da API UniFi.

## Configuração

As métricas são expostas através do django-prometheus e podem ser acessadas no endpoint `/metrics`. Este endpoint requer autenticação de superusuário para garantir a segurança dos dados.

### Instalação

1. O django-prometheus já está instalado e configurado no projeto
2. As métricas são coletadas automaticamente para todas as chamadas à API
3. Para visualizar as métricas, acesse `/metrics` com um usuário superadmin

## Métricas Disponíveis

### Chamadas à API

- **Nome**: `unifi_api_requests_total`
- **Tipo**: Counter
- **Labels**: 
  - `method`: Método da API chamado (ex: add_mac, bulk_add)
  - `status`: Resultado da chamada (success/error)
- **Descrição**: Total de chamadas feitas à API UniFi, segmentadas por método e status

### Latência

- **Nome**: `unifi_api_latency_seconds`
- **Tipo**: Histogram
- **Labels**:
  - `method`: Método da API chamado
- **Buckets**: [0.1, 0.5, 1.0, 2.0, 5.0]
- **Descrição**: Tempo gasto processando chamadas à API, útil para identificar gargalos

### Contagem de MACs

- **Nome**: `unifi_mac_addresses_total`
- **Tipo**: Gauge
- **Descrição**: Número total atual de endereços MAC na whitelist

### Cache

- **Nome**: `unifi_api_cache_hits_total`
- **Tipo**: Counter
- **Descrição**: Número de vezes que informações foram encontradas no cache

- **Nome**: `unifi_api_cache_misses_total`
- **Tipo**: Counter
- **Descrição**: Número de vezes que informações não foram encontradas no cache

### Operações em Lote

- **Nome**: `unifi_api_bulk_operations_total`
- **Tipo**: Counter
- **Labels**:
  - `operation`: Tipo de operação (add/remove)
  - `status`: Resultado da operação (success/error)
- **Descrição**: Número de operações em lote realizadas

## Uso com Prometheus

Para coletar estas métricas com Prometheus, adicione o seguinte job à configuração:

```yaml
scrape_configs:
  - job_name: 'unifi_auth_api'
    scrape_interval: 15s
    metrics_path: '/metrics'
    basic_auth:
      username: 'seu_usuario_admin'
      password: 'sua_senha_admin'
    static_configs:
      - targets: ['localhost:8449']
```

## Dashboards Recomendados

### Latência e Erros
- Taxa de erro por método
- Latência média, p95 e p99 por método
- Top 10 métodos mais lentos

### Cache
- Taxa de hit/miss do cache
- Eficiência do cache ao longo do tempo

### Operações em Lote
- Taxa de sucesso/erro das operações em lote
- Volume de operações em lote por tipo

### Capacidade
- Número total de MACs gerenciados
- Crescimento do número de MACs ao longo do tempo

## Alertas Recomendados

1. **Latência Alta**
   ```
   unifi_api_latency_seconds{quantile="0.95"} > 2.0
   ```

2. **Taxa de Erro Alta**
   ```
   rate(unifi_api_requests_total{status="error"}[5m]) > 0.1
   ```

3. **Cache Ineficiente**
   ```
   rate(unifi_api_cache_misses_total[5m]) / 
   (rate(unifi_api_cache_hits_total[5m]) + rate(unifi_api_cache_misses_total[5m])) > 0.5
   ```

4. **Crescimento Rápido de MACs**
   ```
   delta(unifi_mac_addresses_total[1h]) > 100
   ```
