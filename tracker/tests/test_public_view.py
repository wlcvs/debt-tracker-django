import pytest


@pytest.mark.django_db
def test_public_view_accessible_without_login(client, person, debt, payment):
    response = client.get(f"/public/{person.pk}/")
    assert response.status_code == 200
    assert person.name.encode() in response.content


@pytest.mark.django_db
def test_public_view_shows_debts_and_payments(client, person, debt, payment):
    response = client.get(f"/public/{person.pk}/")
    assert debt.title.encode() in response.content
    assert b"Pix" in response.content


@pytest.mark.django_db
def test_public_view_invalid_id_returns_404(client):
    import uuid
    response = client.get(f"/public/{uuid.uuid4()}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_public_view_does_not_show_other_persons_data(client, person, db):
    from django.contrib.auth.models import User
    from tracker.models import Person, Debt
    from datetime import date

    other_user = User.objects.create_user(username="other2", password="pass")
    other_person = Person.objects.create(name="Outro", user=other_user)
    Debt.objects.create(person=other_person, amount="999", description="Secreto", date=date.today())

    response = client.get(f"/public/{person.pk}/")
    assert b"Secreto" not in response.content
