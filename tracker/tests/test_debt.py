import pytest
from datetime import date


@pytest.mark.django_db
def test_add_debt(auth_client, person):
    response = auth_client.post(f"/dashboard/person/{person.pk}/debt/add/", {
        "title": "Mercadinho",
        "amount": "150.00",
        "description": "",
        "date": date.today().isoformat(),
        "payment_method": "PIX",
    })
    assert response.status_code == 302
    assert person.debts.filter(title="Mercadinho").exists()


@pytest.mark.django_db
def test_edit_debt(auth_client, person, debt):
    auth_client.post(f"/dashboard/person/{person.pk}/debt/{debt.pk}/edit/", {
        "title": "Editado",
        "amount": "200.00",
        "description": "",
        "date": date.today().isoformat(),
    })
    debt.refresh_from_db()
    assert debt.title == "Editado"
    assert debt.amount == 200


@pytest.mark.django_db
def test_delete_debt(auth_client, person, debt):
    pk = debt.pk
    auth_client.post(f"/dashboard/person/{person.pk}/debt/{pk}/delete/")
    from tracker.models import Debt
    assert not Debt.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_debt_description_is_optional(auth_client, person):
    response = auth_client.post(f"/dashboard/person/{person.pk}/debt/add/", {
        "title": "Dívida sem desc",
        "amount": "100.00",
        "description": "",
        "date": date.today().isoformat(),
        "payment_method": "PIX",
    })
    assert response.status_code == 302
    assert person.debts.filter(title="Dívida sem desc", description="").exists()
