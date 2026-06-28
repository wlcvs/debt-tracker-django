import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from tracker.models import Person, CreditCard, Debt, Payment


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **options):
        email = getattr(settings, "ADMIN_EMAIL", "admin@example.com")
        password = getattr(settings, "ADMIN_PASSWORD", "changeme")

        user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser: {email}"))
        else:
            self.stdout.write("Superuser already exists, skipping.")

        card = CreditCard.objects.get_or_create(label="Nubank", user=user)[0]

        people_data = ["João Silva", "Maria Souza", "Carlos Lima"]
        for name in people_data:
            person, _ = Person.objects.get_or_create(name=name, user=user)

            for i in range(3):
                debt_date = date.today() - timedelta(days=random.randint(10, 90))
                method = random.choice([None, "PIX", "CASH"])
                credit_card = card if method is None else None
                Debt.objects.get_or_create(
                    person=person,
                    description=f"Dívida {i + 1}",
                    defaults={
                        "amount": round(random.uniform(50, 500), 2),
                        "date": debt_date,
                        "method": method,
                        "credit_card": credit_card,
                    },
                )

            for i in range(random.randint(1, 2)):
                pay_date = date.today() - timedelta(days=random.randint(1, 9))
                Payment.objects.get_or_create(
                    person=person,
                    date=pay_date,
                    defaults={
                        "amount": round(random.uniform(20, 200), 2),
                        "method": random.choice(["PIX", "CASH"]),
                    },
                )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))
