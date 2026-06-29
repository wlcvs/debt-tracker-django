import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from tracker.models import Person, CreditCard, Debt, Payment


DEBT_SAMPLES = [
    ("Supermercado", "CASH"),
    ("Gasolina", "PIX"),
    ("Restaurante", None),
    ("Farmácia", "PIX"),
    ("Cinema", None),
    ("Lanche", "CASH"),
    ("Material escolar", "PIX"),
    ("Transporte", "CASH"),
    ("Aluguel de ferramenta", None),
    ("Conta de água", "PIX"),
    ("Mercadinho", "CASH"),
    ("Veterinário", None),
]

PAYMENT_SAMPLES = [
    ("Parcela 1", "PIX"),
    ("Parcela 2", "CASH"),
    ("Acerto geral", "PIX"),
    ("", "CASH"),
    ("", "PIX"),
    ("Transferência", "PIX"),
]


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **options):
        email = getattr(settings, "ADMIN_EMAIL", "admin@example.com")
        password = getattr(settings, "ADMIN_PASSWORD", "changeme")

        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser: {email}"))
        else:
            self.stdout.write("Superuser already exists, skipping.")

        card = CreditCard.objects.get_or_create(label="Nubank", user=user)[0]
        card2 = CreditCard.objects.get_or_create(label="Inter", user=user)[0]

        people_data = ["João Silva", "Maria Souza", "Carlos Lima"]
        for name in people_data:
            person, _ = Person.objects.get_or_create(name=name, user=user)

            debt_pool = random.sample(DEBT_SAMPLES, k=min(4, len(DEBT_SAMPLES)))
            for description, method in debt_pool:
                debt_date = date.today() - timedelta(days=random.randint(5, 120))
                if method is None:
                    credit_card = random.choice([card, card2])
                else:
                    credit_card = None
                Debt.objects.get_or_create(
                    person=person,
                    description=description,
                    defaults={
                        "amount": round(random.uniform(30, 600), 2),
                        "date": debt_date,
                        "method": method,
                        "credit_card": credit_card,
                    },
                )

            pay_pool = random.sample(PAYMENT_SAMPLES, k=random.randint(2, 3))
            for description, method in pay_pool:
                pay_date = date.today() - timedelta(days=random.randint(1, 30))
                Payment.objects.get_or_create(
                    person=person,
                    date=pay_date,
                    defaults={
                        "amount": round(random.uniform(20, 250), 2),
                        "description": description,
                        "method": method,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))
