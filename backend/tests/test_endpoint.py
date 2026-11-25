# --- TESTY ENDPOINTU (Wymagane: min. 1) ---

def test_health_endpoint_returns_ok_status(client):
    """Sprawdza, czy endpoint /api/health zwraca status 200 oraz poprawną strukturę JSON."""
    res = client.get('/api/health')

    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}
