from config import application_config, db_config, openapi_config


class TestPing:
    prefix = '/health/ping'

    def test_get_app_status(self, test_client):
        response = test_client.get(self.prefix)
        assert response.status_code == 200
        assert 'pong' in response.text.lower()


class TestSystemStatus:
    prefix = '/health/system-status'

    def test_get_app_status(self, test_client):
        response = test_client.get(self.prefix)
        assert response.status_code == 200
        assert application_config.is_debug == response.json()['debug']
        assert openapi_config.version == response.json()['api_version']


class TestReadProbe:
    prefix = '/health/readiness-probe'

    def test_get_health_status(self, test_client):
        response = test_client.get(self.prefix)
        assert response.status_code == 200
        assert db_config.driver in response.text.lower()


class TestLiveProbe:
    prefix = '/health/liveness-probe'

    def test_get_health_status(self, test_client):
        response = test_client.get(self.prefix)
        assert response.status_code == 200
        assert db_config.driver in response.text.lower()
