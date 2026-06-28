from django.contrib import admin
from .models import Person, CreditCard, Debt, Payment


class DebtInline(admin.TabularInline):
    model = Debt
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "balance", "created_at")
    inlines = [DebtInline, PaymentInline]


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ("label", "user", "created_at")


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ("person", "amount", "description", "date", "method", "credit_card")
    list_filter = ("method", "credit_card")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("person", "amount", "date", "method")
    list_filter = ("method",)
