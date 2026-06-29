from django import forms
from .models import Person, CreditCard, Debt, Payment

INPUT_CLASS = (
    "w-full bg-transparent border border-current/30 px-3 py-2 text-sm "
    "focus:outline-none focus:border-current"
)
SELECT_CLASS = INPUT_CLASS


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
        }


class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ["label"]
        widgets = {
            "label": forms.TextInput(attrs={"class": INPUT_CLASS}),
        }


class DebtForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2, localize=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "inputmode": "decimal"}),
    )

    class Meta:
        model = Debt
        fields = ["title", "amount", "description", "date", "credit_card", "method"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "description": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "date": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
            "credit_card": forms.Select(attrs={"class": SELECT_CLASS}),
            "method": forms.Select(attrs={"class": SELECT_CLASS}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["credit_card"].queryset = CreditCard.objects.filter(user=user)
        self.fields["credit_card"].required = False
        self.fields["method"].required = False
        self.fields["description"].required = False


class PaymentForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2, localize=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "inputmode": "decimal"}),
    )

    class Meta:
        model = Payment
        fields = ["amount", "description", "date", "method"]
        widgets = {
            "description": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "date": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
            "method": forms.Select(attrs={"class": SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False
