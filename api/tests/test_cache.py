import json
from unittest.mock import MagicMock, patch

from cache.redis import get_cached, get_redis, set_cache


def _make_mock_redis():
    mock_client = MagicMock()
    return mock_client


def test_get_redis_creates_client_once():
    """get_redis() initialise le client une seule fois (singleton)."""
    import cache.redis as cache_module

    cache_module._client = None
    with patch("cache.redis.redis.from_url") as mock_from_url:
        mock_from_url.return_value = MagicMock()
        client1 = get_redis()
        client2 = get_redis()

    mock_from_url.assert_called_once()
    assert client1 is client2
    cache_module._client = None


def test_get_cached_returns_parsed_dict():
    """get_cached retourne un dict parsé quand la clé existe."""
    mock_client = MagicMock()
    mock_client.get.return_value = json.dumps({"id": 1, "name": "Bulbizarre"})

    with patch("cache.redis.get_redis", return_value=mock_client):
        result = get_cached("pokemon:1")

    assert result == {"id": 1, "name": "Bulbizarre"}
    mock_client.get.assert_called_once_with("pokemon:1")


def test_get_cached_returns_none_on_miss():
    """get_cached retourne None quand la clé n'existe pas (cache miss)."""
    mock_client = MagicMock()
    mock_client.get.return_value = None

    with patch("cache.redis.get_redis", return_value=mock_client):
        result = get_cached("pokemon:999")

    assert result is None


def test_set_cache_calls_setex():
    """set_cache appelle setex avec le bon TTL et la valeur sérialisée."""
    mock_client = MagicMock()
    data = {"id": 1, "name": "Bulbizarre"}

    with patch("cache.redis.get_redis", return_value=mock_client):
        set_cache("pokemon:1", data, ttl=3600)

    mock_client.setex.assert_called_once_with("pokemon:1", 3600, json.dumps(data))
