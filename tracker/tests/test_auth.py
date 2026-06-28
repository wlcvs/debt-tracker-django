import pytest


@pytest.mark.django_db
def test_dashboard_redirects_unauthenticated(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_login_with_valid_credentials(client, user):
    response = client.post("/login/", {"username": "testuser", "password": "testpass"})
    assert response.status_code == 302
    assert response["Location"] == "/"


@pytest.mark.django_db
def test_login_with_invalid_credentials(client):
    response = client.post("/login/", {"username": "wrong", "password": "wrong"})
    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_requires_post(auth_client):
    response = auth_client.get("/logout/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_logout_redirects_to_login(auth_client):
    response = auth_client.post("/logout/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]
