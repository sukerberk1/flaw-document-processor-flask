def test_features_integration(client):
    """Test interactions between features."""
    # Example test that checks if both features are working together
    response = client.get('/')
    assert response.status_code == 200
