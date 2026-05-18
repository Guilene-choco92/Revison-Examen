"""
Fixtures mock pour l'examen FINAL-AHT20-FORMATIF.

Simule board, busio, adafruit_ahtx0 et requests sans materiel
physique ni reseau. NE PAS MODIFIER.
"""

import sys
from unittest.mock import MagicMock

import pytest


class MockAHTx0:
    """Mock du capteur AHT20 : expose des valeurs plausibles
    qui peuvent etre modifiees par les tests via les attributs
    `_temperature` et `_humidity`.
    """

    def __init__(self, i2c):
        self.i2c = i2c
        self._temperature = 24.5
        self._humidity = 45.0

    @property
    def temperature(self):
        return self._temperature

    @property
    def relative_humidity(self):
        return self._humidity


class MockResponse:
    """Mock minimal de `requests.Response` controlable par les tests."""

    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests import HTTPError
            raise HTTPError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def mock_all_hardware(monkeypatch):
    """Mock board, busio, adafruit_ahtx0 et requests pour le CI."""

    # Mock board module -- distinct pin objects
    mock_board = MagicMock()
    mock_board.D17 = MagicMock(name='board.D17')
    mock_board.SCL = MagicMock(name='board.SCL')
    mock_board.SDA = MagicMock(name='board.SDA')
    mock_board.I2C = MagicMock(return_value=MagicMock(name='I2C_bus'))
    monkeypatch.setitem(sys.modules, 'board', mock_board)

    # Mock busio
    mock_busio = MagicMock()
    monkeypatch.setitem(sys.modules, 'busio', mock_busio)

    # Mock adafruit_ahtx0
    mock_ahtx0 = MagicMock()
    mock_ahtx0.AHTx0 = MockAHTx0
    monkeypatch.setitem(sys.modules, 'adafruit_ahtx0', mock_ahtx0)

    # Mock requests : on intercepte get et post avec MockResponse OK par defaut
    import requests as real_requests

    def fake_get(url, **kwargs):
        return MockResponse(200, {"ok": True, "service": "evaluer-aht20-formatif"})

    def fake_post(url, json=None, **kwargs):
        return MockResponse(200, {
            "decision": "confort",
            "valeur_recue": (json or {}).get("valeur"),
            "seuil_humide": 65.0,
            "seuil_sec": 35.0,
        })

    monkeypatch.setattr(real_requests, 'get', fake_get)
    monkeypatch.setattr(real_requests, 'post', fake_post)

    return {
        'board': mock_board,
        'busio': mock_busio,
        'ahtx0': mock_ahtx0,
        'fake_get': fake_get,
        'fake_post': fake_post,
    }


@pytest.fixture
def mock_time_sleep(monkeypatch):
    """Mock time.sleep pour accelerer les tests."""
    monkeypatch.setattr('time.sleep', lambda s: None)
