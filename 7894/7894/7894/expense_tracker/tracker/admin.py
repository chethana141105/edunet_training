from django.contrib import admin
from .models import (
    Expense, Budget, CategoryBudget, SpendingPersonality, MoodAnalysis,
    MoneyLeak, BurnRatePrediction, MonthlyStory, WhatIfSimulation
)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date', 'mood')
    list_filter = ('category', 'mood', 'date')
    search_fields = ('user__username', 'description')
    ordering = ('-date',)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_budget', 'created_at')
    search_fields = ('user__username',)


@admin.register(CategoryBudget)
class CategoryBudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'budget_amount')
    list_filter = ('category',)
    search_fields = ('user__username',)


@admin.register(SpendingPersonality)
class SpendingPersonalityAdmin(admin.ModelAdmin):
    list_display = ('user', 'personality_type', 'confidence_score', 'last_analyzed')
    list_filter = ('personality_type',)
    search_fields = ('user__username',)


@admin.register(MoodAnalysis)
class MoodAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'category', 'total_spent', 'frequency')
    list_filter = ('mood', 'category', 'period')
    search_fields = ('user__username',)


@admin.register(MoneyLeak)
class MoneyLeakAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'monthly_total', 'severity', 'month')
    list_filter = ('severity', 'month', 'category')
    search_fields = ('user__username',)


@admin.register(BurnRatePrediction)
class BurnRatePredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_month', 'projected_month_total', 'will_overspend')
    list_filter = ('will_overspend',)
    search_fields = ('user__username',)


@admin.register(MonthlyStory)
class MonthlyStoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'total_spent', 'created_at')
    list_filter = ('month',)
    search_fields = ('user__username',)


@admin.register(WhatIfSimulation)
class WhatIfSimulationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'original_total', 'simulated_total', 'savings_percentage')
    search_fields = ('user__username', 'name')
    ordering = ('-created_at',)
