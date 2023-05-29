class TestProductInfo:
    prefix = '/api/v1/product_info/'

    def test_check_auth_negative(self, test_client):
        response = test_client.get(self.prefix + 'count')
        assert response.status_code == 403
        assert 'not authenticated' in response.text.lower()

    def test_check_auth_positive(self, test_client_with_auth_token):
        response = test_client_with_auth_token.get(self.prefix + 'count')
        assert response.status_code != 403
        assert 'not authenticated' not in response.text.lower()

    def test_check_wrong_token(self, test_client_with_auth_token, test_token):
        wrong_token = {key: value + 'x' for key, value in test_token.items()}
        test_client_with_auth_token.headers.update(wrong_token)
        response = test_client_with_auth_token.get(self.prefix + 'count')
        assert response.status_code == 403
        assert 'invalid auth-token' in response.text.lower()
