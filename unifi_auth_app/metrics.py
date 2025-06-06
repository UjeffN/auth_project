from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable, Any

# Métricas para a API UniFi
unifi_api_requests = Counter(
    'unifi_api_requests_total',
    'Total number of requests made to UniFi API',
    ['method', 'status']
)

unifi_api_latency = Histogram(
    'unifi_api_latency_seconds',
    'Time spent processing UniFi API requests',
    ['method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

mac_addresses_total = Gauge(
    'unifi_mac_addresses_total',
    'Total number of MAC addresses in whitelist'
)

cache_hits = Counter(
    'unifi_api_cache_hits_total',
    'Number of cache hits for SSID info'
)

cache_misses = Counter(
    'unifi_api_cache_misses_total',
    'Number of cache misses for SSID info'
)

bulk_operations = Counter(
    'unifi_api_bulk_operations_total',
    'Number of bulk operations performed',
    ['operation', 'status']
)

def track_api_call(method: str) -> Callable:
    """
    Decorator para monitorar chamadas à API do UniFi.
    Registra latência e status das chamadas.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                unifi_api_requests.labels(
                    method=method,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                unifi_api_requests.labels(
                    method=method,
                    status='error'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                unifi_api_latency.labels(method=method).observe(duration)
        return wrapper
    return decorator

def track_cache_access(hit: bool) -> None:
    """
    Registra hits e misses do cache
    """
    if hit:
        cache_hits.inc()
    else:
        cache_misses.inc()

def track_bulk_operation(operation: str, success: bool) -> None:
    """
    Registra operações em lote
    """
    status = 'success' if success else 'error'
    bulk_operations.labels(
        operation=operation,
        status=status
    ).inc()

def update_mac_count(count: int) -> None:
    """
    Atualiza o contador total de MACs
    """
    mac_addresses_total.set(count)
