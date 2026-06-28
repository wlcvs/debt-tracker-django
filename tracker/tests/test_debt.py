import pytest
from datetime import date


@pytest.mark.django_db
def test_add_debt(auth_client, person):
    response = auth_client.post(f"/person/{person.pk}/debt/add/", {
        "amount": "150.00",
        "description": "Aluguel",
        "date": date.today().isoformat(),
    })
    assert response.status_code == 302
    assert person.debts.filter(description="Aluguel").exists()


@pytest.mark.django_db
def test_edit_debt(auth_client, person, debt):
    auth_client.post(f"/person/{person.pk}/debt/{debt.pk}/edit/", {
        "amount": "200.00",
        "description": "Editado",
        "date": date.today().isoformat(),
    })
    debt.refresh_from_db()
    assert debt.description == "Editado"
    assert debt.amount == 200


@pytest.mark.django_db
def test_delete_debt(auth_client, person, debt):
    pk = debt.pk
    auth_client.post(f"/person/{person.pk}/debt/{pk}/delete/")
    from tracker.models import Debt
    assert not Debt.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_debt_requires_description(auth_client, person):
    response = auth_client.post(f"/person/{person.pk}/debt/add/", {
        "amount": "100.00",
        "description": "",
        "date": date.today().isoformat(),
    })
    assert response.status_code == 302
    assert not person.debts.exists()
