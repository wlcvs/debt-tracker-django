import pytest
from datetime import date
from django.contrib.auth.models import User
from tracker.models import Person, CreditCard, Debt, Payment


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def auth_client(client, user):
    client.login(username="testuser", password="testpass")
    return client


@pytest.fixture
def person(user):
    return Person.objects.create(name="João Silva", user=user)


@pytest.fixture
def credit_card(user):
    return CreditCard.objects.create(label="Nubank", user=user)


@pytest.fixture
def debt(person, credit_card):
    return Debt.objects.create(
        person=person,
        amount="100.00",
        description="Teste",
        date=date.today(),
    )


@pytest.fixture
def payment(person):
    return Payment.objects.create(
        person=person,
        amount="50.00",
        date=date.today(),
        method="PIX",
    )
