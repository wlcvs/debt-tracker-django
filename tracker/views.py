from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CreditCardForm, DebtForm, PaymentForm, PersonForm
from .models import CreditCard, Debt, Payment, Person


class AppLoginView(LoginView):
    template_name = "tracker/login.html"
    redirect_authenticated_user = True


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


# ── Dashboard ──────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save(commit=False)
            person.user = request.user
            person.save()
            return redirect("dashboard")
    else:
        form = PersonForm()

    people = (
        Person.objects.filter(user=request.user)
        .annotate(
            total_debt=Coalesce(Sum("debts__amount"), Decimal("0")),
            total_paid=Coalesce(Sum("payments__amount"), Decimal("0")),
        )
        .order_by("name")
    )
    for p in people:
        p.balance = p.total_debt - p.total_paid

    total_to_receive = sum(p.balance for p in people)
    active_debtors = sum(1 for p in people if p.balance > 0)

    total_paid_sum = Payment.objects.filter(
        person__user=request.user
    ).aggregate(s=Coalesce(Sum("amount"), Decimal("0")))["s"]

    stats = {
        "total_to_receive": total_to_receive,
        "active_debtors": active_debtors,
        "total_debtors": len(people),
        "total_debts": Debt.objects.filter(person__user=request.user).count(),
        "total_payments": Payment.objects.filter(person__user=request.user).count(),
        "total_paid": total_paid_sum,
    }

    from django.db.models import Count
    credit_cards = CreditCard.objects.filter(user=request.user).annotate(
        debt_count=Count("debts")
    ).order_by("label")

    return render(request, "tracker/dashboard.html", {
        "people": people,
        "stats": stats,
        "credit_cards": credit_cards,
        "form": form,
        "card_form": CreditCardForm(),
    })


# ── Person ─────────────────────────────────────────────────────────────────────

@login_required
def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    debts = person.debts.select_related("credit_card").order_by("-date")
    payments = person.payments.order_by("-date")
    total_debt = sum(d.amount for d in debts)
    total_paid = sum(p.amount for p in payments)

    return render(request, "tracker/person_detail.html", {
        "person": person,
        "debts": debts,
        "payments": payments,
        "balance": total_debt - total_paid,
        "total_debt": total_debt,
        "total_paid": total_paid,
        "debt_form": DebtForm(user=request.user),
        "payment_form": PaymentForm(),
        "person_form": PersonForm(instance=person),
    })


@login_required
@require_POST
def edit_person(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    form = PersonForm(request.POST, instance=person)
    if form.is_valid():
        form.save()
    return redirect("person_detail", pk=pk)


@login_required
@require_POST
def delete_person(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    person.delete()
    return redirect("dashboard")


# ── Debt ───────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_debt(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    form = DebtForm(request.POST, user=request.user)
    if form.is_valid():
        debt = form.save(commit=False)
        debt.person = person
        debt.save()
    return redirect("person_detail", pk=pk)


@login_required
def edit_debt(request, pk, debt_id):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    debt = get_object_or_404(Debt, pk=debt_id, person=person)
    if request.method == "POST":
        form = DebtForm(request.POST, instance=debt, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("person_detail", pk=pk)
    else:
        form = DebtForm(instance=debt, user=request.user)
    return render(request, "tracker/edit_form.html", {
        "form": form,
        "title": "Editar dívida",
        "back_url": f"/person/{pk}/",
    })


@login_required
@require_POST
def delete_debt(request, pk, debt_id):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    debt = get_object_or_404(Debt, pk=debt_id, person=person)
    debt.delete()
    return redirect("person_detail", pk=pk)


# ── Payment ────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_payment(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    form = PaymentForm(request.POST)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.person = person
        payment.save()
    return redirect("person_detail", pk=pk)


@login_required
def edit_payment(request, pk, payment_id):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    payment = get_object_or_404(Payment, pk=payment_id, person=person)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect("person_detail", pk=pk)
    else:
        form = PaymentForm(instance=payment)
    return render(request, "tracker/edit_form.html", {
        "form": form,
        "title": "Editar pagamento",
        "back_url": f"/person/{pk}/",
    })


@login_required
@require_POST
def delete_payment(request, pk, payment_id):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    payment = get_object_or_404(Payment, pk=payment_id, person=person)
    payment.delete()
    return redirect("person_detail", pk=pk)


# ── Credit Card ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_credit_card(request):
    form = CreditCardForm(request.POST)
    if form.is_valid():
        card = form.save(commit=False)
        card.user = request.user
        card.save()
    return redirect("dashboard")


@login_required
def edit_credit_card(request, card_id):
    card = get_object_or_404(CreditCard, pk=card_id, user=request.user)
    if request.method == "POST":
        form = CreditCardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = CreditCardForm(instance=card)
    return render(request, "tracker/edit_form.html", {
        "form": form,
        "title": "Editar cartão",
        "back_url": "/dashboard/",
    })


@login_required
@require_POST
def delete_credit_card(request, card_id):
    card = get_object_or_404(CreditCard, pk=card_id, user=request.user)
    if card.debts.exists():
        return redirect("dashboard")
    card.delete()
    return redirect("dashboard")


# ── Public landing ─────────────────────────────────────────────────────────────

def custom_404(request, exception=None, **kwargs):
    return render(request, "404.html", status=404)


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("public_landing")


def public_landing(request):
    error = False
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        try:
            person = Person.objects.get(pk=code)
            return redirect("public_view", pk=person.pk)
        except (Person.DoesNotExist, ValueError):
            error = True
    return render(request, "tracker/public_landing.html", {"error": error})


# ── Public view ────────────────────────────────────────────────────────────────

def public_view(request, pk):
    person = get_object_or_404(Person, pk=pk)
    debts = person.debts.select_related("credit_card").order_by("-date")
    payments = person.payments.order_by("-date")
    total_debt = sum(d.amount for d in debts)
    total_paid = sum(p.amount for p in payments)

    return render(request, "tracker/public_view.html", {
        "person": person,
        "debts": debts,
        "payments": payments,
        "balance": total_debt - total_paid,
        "total_debt": total_debt,
        "total_paid": total_paid,
    })
