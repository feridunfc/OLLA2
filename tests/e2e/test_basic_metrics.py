import requests, pytest
def test_healthz(): assert requests.get('http://localhost:8000/healthz').status_code == 200
def test_metrics(): assert 'olla2_requests_total' in requests.get('http://localhost:8000/metrics').text
