from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import statistics


# =========================
# GLOBAL CONSTANTS
# =========================
CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('INR', 'Indian Rupee'),
    ('JPY', 'Japanese Yen'),
    ('AUD', 'Australian Dollar'),
    ('CAD', 'Canadian Dollar'),
    ('CHF', 'Swiss Franc'),
    ('CNY', 'Chinese Yuan'),
    ('SEK', 'Swedish Krona'),
]


# =========================
# GLOBAL CATEGORY (OPTION A)
# =========================
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for auto-categorization")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================
# OVERALL MONTHLY BUDGET
# =========================
class Budget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='budget')
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    leak_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Budget for {self.user.username}"


# =========================
# CATEGORY-WISE BUDGET
# =========================
class CategoryBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_budgets')
    budget_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'category')
        ordering = ['category']

    def __str__(self):
        return f"{self.category.name} - {self.user.username}"


# =========================
# EXPENSES
# =========================
class Expense(models.Model):
    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('neutral', 'Neutral'),
        ('stressed', 'Stressed'),
    ]

# Moved to module level for shared use
# CURRENCY_CHOICES = ...

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='expenses')
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='neutral')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.currency} {self.amount} - {self.date}"

    def get_amount_in_currency(self, target_currency):
        """Convert this expense amount to target currency."""
        from .utils import convert_currency
        return convert_currency(self.amount, self.currency, target_currency)


# =========================
# BANK ACCOUNT INTEGRATION
# =========================
class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
        ('credit', 'Credit Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)  # Masked in UI
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    last_synced = models.DateTimeField(null=True, blank=True)
    is_linked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({self.user.username})"


# =========================
# TRANSACTIONS
# =========================
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    description = models.TextField()
    merchant_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    
    # Link to Expense for double-entry tracking (optional but useful)
    expense = models.OneToOneField('Expense', on_delete=models.SET_NULL, null=True, blank=True, related_name='transaction_ref')
    
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    original_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.merchant_name} - {self.amount} {self.currency}"


# =========================
# SPENDING PERSONALITY
# =========================
class SpendingPersonality(models.Model):
    PERSONALITY_TYPES = [
        ('planner', 'Planner'),
        ('impulse_spender', 'Impulse Spender'),
        ('minimalist', 'Minimalist'),
        ('balanced', 'Balanced'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='spending_personality')
    personality_type = models.CharField(max_length=20, choices=PERSONALITY_TYPES)
    variance_score = models.FloatField(default=0)
    category_diversity = models.FloatField(default=0)
    weekend_vs_weekday_ratio = models.FloatField(default=0)
    last_analyzed = models.DateTimeField(auto_now=True)
    confidence_score = models.FloatField(default=0)  # 0–100

    class Meta:
        ordering = ['-last_analyzed']

    def __str__(self):
        return f"{self.user.username} - {self.get_personality_type_display()}"


# =========================
# MOOD ANALYSIS (SNAPSHOT)
# =========================
class MoodAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_analyses')
    mood = models.CharField(max_length=20)
    category = models.CharField(max_length=50)  # snapshot
    average_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frequency = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    period = models.CharField(max_length=20, default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'mood', 'category', 'period')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.mood} - {self.category}"


# =========================
# MONEY LEAK DETECTION
# =========================
class MoneyLeak(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='money_leaks')
    category = models.CharField(max_length=50)  # snapshot
    monthly_total = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = models.IntegerField()
    average_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    frequency_description = models.CharField(max_length=100)
    month = models.DateField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'category', 'month')
        ordering = ['-month', '-monthly_total']

    def __str__(self):
        return f"{self.user.username} - {self.category} - ${self.monthly_total}"


# =========================
# BURN RATE PREDICTION
# =========================
class BurnRatePrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='burn_rate_predictions')
    current_month = models.DateField()
    daily_average_spend = models.DecimalField(max_digits=10, decimal_places=2)
    projected_month_total = models.DecimalField(max_digits=10, decimal_places=2)
    budget_amount = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_exhaustion_date = models.DateField(null=True, blank=True)
    will_overspend = models.BooleanField(default=False)
    overspend_percentage = models.FloatField(default=0)
    savings_percentage = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-current_month']

    def __str__(self):
        return f"{self.user.username} - {self.current_month.strftime('%B %Y')}"


# =========================
# MONTHLY STORY
# =========================
class MonthlyStory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_stories')
    month = models.DateField()
    narrative = models.TextField()
    top_category = models.CharField(max_length=50)
    top_category_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)
    budget_vs_actual = models.CharField(max_length=100)
    emotional_trend = models.CharField(max_length=100)
    money_leak_alerts = models.JSONField(default=list, blank=True)
    key_insights = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.user.username} - {self.month.strftime('%B %Y')}"


# =========================
# WHAT-IF SIMULATIONS
# =========================
class WhatIfSimulation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulations')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    adjustments = models.JSONField()
    original_total = models.DecimalField(max_digits=10, decimal_places=2)
    simulated_total = models.DecimalField(max_digits=10, decimal_places=2)
    savings = models.DecimalField(max_digits=10, decimal_places=2)
    savings_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"
