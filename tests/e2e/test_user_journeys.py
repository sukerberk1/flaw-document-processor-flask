def test_complete_user_journey(client):
    """Test a complete user journey through the application."""
    # Visit homepage
    response = client.get('/')
    assert response.status_code == 200
    
    # Navigate to feature one
    response = client.get('/feature-one/')
    assert response.status_code == 200
    
    # Navigate to feature two
    response = client.get('/feature-two/')
    assert response.status_code == 200
