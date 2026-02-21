from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Expense, Budget, Category  # ✅ IMPORT CATEGORY


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
        )


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'currency', 'category', 'date', 'description', 'mood']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount',
                'step': '0.01'
            }),
            'currency': forms.Select(),
            'category': forms.Select(),  # dropdown
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Description',
                'rows': 3
            }),
            'mood': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ THIS IS THE KEY FIX
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Select a category"


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['monthly_budget', 'currency', 'leak_threshold']
        widgets = {
            'monthly_budget': forms.NumberInput(attrs={
                'placeholder': 'Monthly Budget',
                'step': '0.01'
            }),
            'currency': forms.Select(),
            'leak_threshold': forms.NumberInput(attrs={
                'placeholder': 'Leak Threshold (e.g. 5.00)',
                'step': '0.01'
            }),
        }
