import uuid
from django.db import models
from django.contrib.auth.models import User


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="people")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def balance(self):
        total_debt = sum(d.amount for d in self.debts.all())
        total_paid = sum(p.amount for p in self.payments.all())
        return total_debt - total_paid


class CreditCard(models.Model):
    label = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credit_cards")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label


class Debt(models.Model):
    class Method(models.TextChoices):
        PIX = "PIX", "Pix"
        CASH = "CASH", "Dinheiro"

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="debts")
    credit_card = models.ForeignKey(
        CreditCard, on_delete=models.SET_NULL, null=True, blank=True, related_name="debts"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default="")
    description = models.CharField(max_length=500, blank=True, default="")
    date = models.DateField()
    method = models.CharField(max_length=4, choices=Method.choices, null=True, blank=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.person} — R$ {self.amount}"


class Statement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="statements")
    bank = models.CharField(max_length=100)
    filename = models.CharField(max_length=255)
    pdf_data = models.BinaryField()
    transaction_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.bank} — {self.filename}"


class Payment(models.Model):
    class Method(models.TextChoices):
        PIX = "PIX", "Pix"
        CASH = "CASH", "Dinheiro"

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=500, blank=True, default="")
    date = models.DateField()
    method = models.CharField(max_length=4, choices=Method.choices, default=Method.CASH)

    def __str__(self):
        return f"{self.person} — R$ {self.amount}"
