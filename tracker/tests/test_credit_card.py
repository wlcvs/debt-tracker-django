import pytest


@pytest.mark.django_db
def test_add_credit_card(auth_client, user):
    auth_client.post("/dashboard/credit-card/add/", {"label": "Itaú"})
    from tracker.models import CreditCard
    assert CreditCard.objects.filter(label="Itaú", user=user).exists()


@pytest.mark.django_db
def test_edit_credit_card(auth_client, credit_card):
    auth_client.post(f"/dashboard/credit-card/{credit_card.pk}/edit/", {"label": "Bradesco"})
    credit_card.refresh_from_db()
    assert credit_card.label == "Bradesco"


@pytest.mark.django_db
def test_delete_credit_card_without_debts(auth_client, credit_card):
    pk = credit_card.pk
    auth_client.post(f"/dashboard/credit-card/{pk}/delete/")
    from tracker.models import CreditCard
    assert not CreditCard.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_delete_credit_card_with_debts_is_blocked(auth_client, credit_card, debt):
    debt.credit_card = credit_card
    debt.save()
    pk = credit_card.pk
    auth_client.post(f"/dashboard/credit-card/{pk}/delete/")
    from tracker.models import CreditCard
    assert CreditCard.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_card_label_required(auth_client):
    response = auth_client.post("/dashboard/credit-card/add/", {"label": ""})
    assert response.status_code == 302
    from tracker.models import CreditCard
    assert not CreditCard.objects.exists()
