from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
def get_metrics():
    return generate_latest(REGISTRY)