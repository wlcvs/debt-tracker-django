import pytest


@pytest.mark.django_db
def test_dashboard_lists_people(auth_client, person):
    response = auth_client.get("/")
    assert response.status_code == 200
    assert person.name.encode() in response.content


@pytest.mark.django_db
def test_create_person(auth_client, user):
    response = auth_client.post("/", {"name": "Maria Souza"})
    assert response.status_code == 302
    from tracker.models import Person
    assert Person.objects.filter(name="Maria Souza", user=user).exists()


@pytest.mark.django_db
def test_person_detail_accessible(auth_client, person):
    response = auth_client.get(f"/person/{person.pk}/")
    assert response.status_code == 200
    assert person.name.encode() in response.content


@pytest.mark.django_db
def test_edit_person_name(auth_client, person):
    auth_client.post(f"/person/{person.pk}/edit/", {"name": "Novo Nome"})
    person.refresh_from_db()
    assert person.name == "Novo Nome"


@pytest.mark.django_db
def test_delete_person(auth_client, person):
    pk = person.pk
    auth_client.post(f"/person/{pk}/delete/")
    from tracker.models import Person
    assert not Person.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_person_detail_not_accessible_by_other_user(client, person, db):
    from django.contrib.auth.models import User
    other = User.objects.create_user(username="other", password="pass")
    client.login(username="other", password="pass")
    response = client.get(f"/person/{person.pk}/")
    assert response.status_code == 404
