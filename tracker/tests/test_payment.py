import pytest
from datetime import date


@pytest.mark.django_db
def test_add_payment(auth_client, person):
    response = auth_client.post(f"/person/{person.pk}/payment/add/", {
        "amount": "75.00",
        "date": date.today().isoformat(),
        "method": "PIX",
    })
    assert response.status_code == 302
    assert person.payments.filter(amount="75.00").exists()


@pytest.mark.django_db
def test_edit_payment(auth_client, person, payment):
    auth_client.post(f"/person/{person.pk}/payment/{payment.pk}/edit/", {
        "amount": "99.00",
        "date": date.today().isoformat(),
        "method": "CASH",
    })
    payment.refresh_from_db()
    assert payment.amount == 99
    assert payment.method == "CASH"


@pytest.mark.django_db
def test_delete_payment(auth_client, person, payment):
    pk = payment.pk
    auth_client.post(f"/person/{person.pk}/payment/{pk}/delete/")
    from tracker.models import Payment
    assert not Payment.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_payment_requires_method(auth_client, person):
    response = auth_client.post(f"/person/{person.pk}/payment/add/", {
        "amount": "50.00",
        "date": date.today().isoformat(),
        "method": "",
    })
    assert response.status_code == 302
    assert not person.payments.exists()
