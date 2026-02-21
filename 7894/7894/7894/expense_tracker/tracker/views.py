from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import csv
from io import StringIO
from .models import Budget
import random



from .models import (
    Expense, Budget, CategoryBudget, SpendingPersonality, MoodAnalysis,
    MoneyLeak, BurnRatePrediction, MonthlyStory, WhatIfSimulation
)
from .forms import ExpenseForm, SignUpForm, BudgetForm
from .utils import (
    analyze_spending_personality, analyze_mood_patterns, detect_money_leaks,
    predict_burn_rate, generate_monthly_story, convert_currency, get_supported_currencies,
    get_currency_symbol, sync_bank_account
)
from .models import BankAccount



def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Budget.objects.create(user=user, monthly_budget=3000)
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'auth/signup.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    current_month = timezone.now()
    month_start = current_month.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get monthly expenses
    monthly_expenses = Expense.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lte=month_end.date()
    )
    
    # Get budget info
    budget, created = Budget.objects.get_or_create(
        user=request.user,
        defaults={"monthly_budget": 0, "currency": "USD"}
    )
    target_currency = budget.currency

    # Calculate total spent with currency conversion
    total_spent = Decimal(0)
    for expense in monthly_expenses:
        total_spent += convert_currency(expense.amount, expense.currency, target_currency)
    
    remaining_budget = budget.monthly_budget - total_spent
    budget_percentage = (total_spent / budget.monthly_budget * 100) if budget.monthly_budget > 0 else 0
    
    # Category breakdown with currency conversion
    # create a dict to store totals per category
    category_totals = {}
    
    for expense in monthly_expenses:
        cat_name = expense.category.name
        converted_amount = convert_currency(expense.amount, expense.currency, target_currency)
        
        if cat_name not in category_totals:
            category_totals[cat_name] = {'total': Decimal(0), 'count': 0}
        
        category_totals[cat_name]['total'] += converted_amount
        category_totals[cat_name]['count'] += 1
    
    # Convert properly for template
    category_breakdown = [
        {'category': cat, 'total': data['total'], 'count': data['count']}
        for cat, data in category_totals.items()
    ]
    # Sort
    category_breakdown.sort(key=lambda x: x['total'], reverse=True)
    
    # Recent expenses
    recent_expenses = monthly_expenses[:5]
    
    # Get personality
    personality = SpendingPersonality.objects.filter(user=user).first()
    
    # Ensure burn rate prediction is up to date
    burn_rate = predict_burn_rate(user)
    
    context = {
        'total_spent': total_spent,
        'budget': budget.monthly_budget,
        'currency': get_currency_symbol(target_currency),
        'remaining_budget': remaining_budget,
        'budget_percentage': budget_percentage,
        'category_breakdown': category_breakdown,
        'recent_expenses': recent_expenses,
        'personality': personality,
        'burn_rate': burn_rate,
        'month': current_month,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def expense_list(request):
    user = request.user
    expenses = Expense.objects.filter(user=user)
    
    # Filtering
    category = request.GET.get('category')
    mood = request.GET.get('mood')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    amount_min = request.GET.get('amount_min')
    amount_max = request.GET.get('amount_max')
    
    if category:
        expenses = expenses.filter(category__name=category)
    if mood:
        expenses = expenses.filter(mood=mood)
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    if amount_min:
        expenses = expenses.filter(amount__gte=amount_min)
    if amount_max:
        expenses = expenses.filter(amount__lte=amount_max)
    
    from .models import Category
    categories = Category.objects.all().values_list('name', flat=True)
    moods = [choice[0] for choice in settings.MOOD_CHOICES]
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'moods': moods,
    }
    
    return render(request, 'tracker/expense_list.html', context)


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense_list')
    else:
        # Set default currency from budget
        try:
            budget = Budget.objects.get(user=request.user)
            initial_currency = budget.currency
        except Budget.DoesNotExist:
            initial_currency = 'USD'
            
        form = ExpenseForm(initial={'currency': initial_currency})
    
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'tracker/expense_form.html', {'form': form, 'expense': expense, 'title': 'Edit Expense'})


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        expense.delete()
        return redirect('expense_list')
    
    return render(request, 'tracker/expense_confirm_delete.html', {'expense': expense})


@login_required
def budget_settings(request):
    budget = Budget.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = BudgetForm(instance=budget)
    
    return render(request, 'tracker/budget_settings.html', {'form': form, 'budget': budget})


@login_required
def bank_accounts(request):
    """View linked bank accounts and transactions."""
    user = request.user
    accounts = BankAccount.objects.filter(user=user)
    
    # Check if we need to auto-sync (e.g., if user clicks "Sync Now")
    if request.method == 'POST' and 'sync_account_id' in request.POST:
        account_id = request.POST.get('sync_account_id')
        sync_bank_account(account_id)
        return redirect('bank_accounts')

    context = {
        'accounts': accounts,
    }
    return render(request, 'tracker/bank_accounts.html', context)


@login_required
def link_bank_account(request):
    """Simulate linking a bank account."""
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        account_type = request.POST.get('account_type')
        currency = request.POST.get('currency', 'USD')
        
        # Simulate OAuth flow details
        account_number = f"****{random.randint(1000, 9999)}"
        balance = random.uniform(1000, 50000)
        
        account = BankAccount.objects.create(
            user=request.user,
            bank_name=bank_name,
            account_number=account_number,
            account_type=account_type,
            balance=Decimal(balance).quantize(Decimal('0.01')),
            currency=currency,
            is_linked=True
        )
        
        # Initial Sync
        sync_bank_account(account.id)
        
        return redirect('bank_accounts')
        
    return render(request, 'tracker/link_bank_account.html')


@login_required
def unlink_bank_account(request, pk):
    account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
        return redirect('bank_accounts')
    return redirect('bank_accounts')



@login_required
def category_budget_settings(request):
    user = request.user
    category_budgets = CategoryBudget.objects.filter(user=user)
    categories = [choice[0] for choice in settings.EXPENSE_CATEGORIES]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle delete action
        if action == 'delete':
            budget_id = request.POST.get('id')
            if budget_id:
                CategoryBudget.objects.filter(id=budget_id, user=user).delete()
                return redirect('category_budget_settings')
        
        # Handle create/update action
        else:
            category = request.POST.get('category')
            budget_amount = request.POST.get('budget_amount')
            
            if category and budget_amount:
                CategoryBudget.objects.update_or_create(
                    user=user,
                    category=category,
                    defaults={'budget_amount': budget_amount}
                )
                return redirect('category_budget_settings')
    
    try:
        currency_code = Budget.objects.get(user=user).currency
    except Budget.DoesNotExist:
        currency_code = 'USD'
    currency = get_currency_symbol(currency_code)

    context = {
        'category_budgets': category_budgets,
        'available_categories': categories,
        'currency': currency,
    }
    
    return render(request, 'tracker/category_budget_settings.html', context)


@login_required
def personality_insights(request):
    user = request.user
    
    # Analyze spending patterns
    personality = analyze_spending_personality(user)
    
    context = {
        'personality': personality,
    }
    
    return render(request, 'tracker/insights/personality.html', context)


@login_required
def mood_insights(request):
    user = request.user
    
    # Analyze mood patterns
    mood_data = analyze_mood_patterns(user)
    
    try:
        currency_code = Budget.objects.get(user=user).currency
    except Budget.DoesNotExist:
        currency_code = 'USD'
    currency = get_currency_symbol(currency_code)

    context = {
        'mood_data': mood_data,
        'currency': currency,
    }
    
    return render(request, 'tracker/insights/mood.html', context)


@login_required
def money_leak_insights(request):
    user = request.user
    current_month = timezone.now().replace(day=1)
    
    # Detect money leaks
    leaks = detect_money_leaks(user, current_month)
    
    try:
        currency_code = Budget.objects.get(user=user).currency
    except Budget.DoesNotExist:
        currency_code = 'USD'
    currency = get_currency_symbol(currency_code)

    context = {
        'leaks': leaks,
        'month': current_month,
        'currency': currency,
    }
    
    return render(request, 'tracker/insights/money_leak.html', context)


@login_required
def burn_rate_insights(request):
    user = request.user

    # Predict burn rate
    prediction = predict_burn_rate(user)

    burn_percentage = 0
    burn_percentage_rounded = 0

    if prediction and prediction.budget_amount and prediction.budget_amount > 0:
        burn_percentage = (
            prediction.projected_month_total / prediction.budget_amount
        ) * 100
        burn_percentage_rounded = round(burn_percentage)

    try:
        currency_code = Budget.objects.get(user=user).currency
    except Budget.DoesNotExist:
        currency_code = 'USD'
    currency = get_currency_symbol(currency_code)

    # Calculate delta amounts for display
    overspend_amount = 0
    savings_amount = 0
    suggested_reduction = 0
    
    current_date = timezone.now()
    month_end = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    days_remaining = (month_end.date() - current_date.date()).days
    if days_remaining <= 0:
        days_remaining = 1

    if prediction:
        if prediction.will_overspend:
            overspend_amount = prediction.projected_month_total - prediction.budget_amount
            suggested_reduction = overspend_amount / days_remaining
        else:
            savings_amount = prediction.budget_amount - prediction.projected_month_total

    context = {
        'prediction': prediction,
        'burn_percentage': round(burn_percentage, 2),
        'burn_percentage_rounded': burn_percentage_rounded,
        'overspend_amount': overspend_amount,
        'savings_amount': savings_amount,
        'suggested_reduction': suggested_reduction,
        'days_remaining': days_remaining,
        'currency': currency,
    }

    return render(request, 'tracker/insights/burn_rate.html', context)

@login_required
def monthly_story(request):
    user = request.user
    month = request.GET.get('month')
    
    if not month:
        month = timezone.now().replace(day=1)
    else:
        month = datetime.strptime(month, '%Y-%m-%d').date()
    
    story = MonthlyStory.objects.filter(user=user, month=month).first()
    
    if not story:
        story = generate_monthly_story(user, month)
    
    try:
        currency_code = Budget.objects.get(user=user).currency
    except Budget.DoesNotExist:
        currency_code = 'USD'
    currency = get_currency_symbol(currency_code)

    context = {
        'story': story,
        'month': month,
        'currency': currency,
    }
    
    return render(request, 'tracker/insights/monthly_story.html', context)


@login_required
def what_if_simulator(request):
    user = request.user
    current_month = timezone.now()
    month_start = current_month.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get expenses
    expenses = Expense.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lte=month_end.date()
    )
    
    # Get target currency
    try:
        currency_code = Budget.objects.get(user=user).currency
    except Budget.DoesNotExist:
        currency_code = 'USD'
    
    # Aggregate with conversion
    totals = {}
    for expense in expenses:
        cat_name = expense.category.name if expense.category else 'Uncategorized'
        
        converted = convert_currency(expense.amount, expense.currency, currency_code)
        
        totals[cat_name] = totals.get(cat_name, Decimal(0)) + converted
        
    monthly_expenses = [
        {'category': cat, 'total': total} 
        for cat, total in totals.items()
    ]
    monthly_expenses.sort(key=lambda x: x['total'], reverse=True)
    
    currency_symbol = get_currency_symbol(currency_code)

    context = {
        'expenses_by_category': monthly_expenses,
        'currency': currency_symbol,
    }
    
    return render(request, 'tracker/simulator/what_if.html', context)


@login_required
@require_http_methods(["GET"])
def expense_data_api(request):
    user = request.user
    
    period = request.GET.get('period', 'month')
    current_date = timezone.now()
    
    if period == 'week':
        start_date = current_date - timedelta(days=7)
    elif period == 'month':
        start_date = current_date.replace(day=1)
    elif period == 'year':
        start_date = current_date.replace(month=1, day=1)
    else:
        start_date = current_date.replace(day=1)
    
    expenses = Expense.objects.filter(
        user=user,
        date__gte=start_date.date()
    ).values('date').annotate(total=Sum('amount')).order_by('date')
    
    data = [{'date': e['date'].isoformat(), 'total': str(e['total'])} for e in expenses]
    
    return JsonResponse({'expenses': data})


@login_required
@require_http_methods(["GET"])
def chart_data_api(request):
    user = request.user
    
    current_month = timezone.now()
    month_start = current_month.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Category breakdown
    category_data = Expense.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lte=month_end.date()
    ).values('category').annotate(total=Sum('amount')).order_by('-total')
    
    categories = [item['category'] for item in category_data]
    amounts = [str(item['total']) for item in category_data]
    
    return JsonResponse({
        'categories': categories,
        'amounts': amounts,
    })


@login_required
@require_http_methods(["POST"])
def simulator_api(request):
    user = request.user
    
    try:
        data = json.loads(request.body)
        adjustments = data.get('adjustments', {})
        
        current_month = timezone.now()
        month_start = current_month.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        expenses = Expense.objects.filter(
            user=user,
            date__gte=month_start.date(),
            date__lte=month_end.date()
        )
        
        original_total = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        simulated_total = Decimal(0)
        
        for expense in expenses:
            adjustment = Decimal(str(adjustments.get(expense.category, 0))) / 100
            adjusted_amount = expense.amount * (1 - adjustment)
            simulated_total += adjusted_amount
        
        savings = original_total - simulated_total
        savings_percentage = (savings / original_total * 100) if original_total > 0 else 0
        
        return JsonResponse({
            'original_total': str(original_total),
            'simulated_total': str(simulated_total),
            'savings': str(savings),
            'savings_percentage': round(savings_percentage, 2),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def export_csv(request):
    user = request.user
    expenses = Expense.objects.filter(user=user)
    
    response = StringIO()
    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Amount', 'Currency', 'Description', 'Mood'])
    
    for expense in expenses:
        writer.writerow([
            expense.date,
            expense.category,
            expense.amount,
            expense.currency,
            expense.description,
            expense.mood,
        ])
    
    response_obj = StringIO(response.getvalue())
    response_obj.seek(0)
    
    from django.http import HttpResponse
    response = HttpResponse(response_obj, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    
    return response


# =============================
# CURRENCY CONVERSION ENDPOINTS
# =============================

@login_required
@require_http_methods(["POST"])
def convert_currency_api(request):
    """Convert an amount from one currency to another."""
    user = request.user
    
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        from_currency = data.get('from_currency', 'USD')
        to_currency = data.get('to_currency', 'USD')
        
        converted_amount = convert_currency(amount, from_currency, to_currency)
        
        return JsonResponse({
            'original_amount': str(amount),
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': str(converted_amount),
        })
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@require_http_methods(["GET"])
def supported_currencies_api(request):
    """Get list of supported currencies."""
    user = request.user
    
    currencies = get_supported_currencies()
    return JsonResponse({'currencies': currencies})


@login_required
@require_http_methods(["GET"])
def expense_total_in_currency(request):
    """Get total expenses converted to specified currency."""
    user = request.user
    
    target_currency = request.GET.get('currency', 'USD')
    period = request.GET.get('period', 'month')
    
    try:
        current_date = timezone.now()
        
        if period == 'week':
            start_date = current_date - timedelta(days=7)
        elif period == 'month':
            start_date = current_date.replace(day=1)
        elif period == 'year':
            start_date = current_date.replace(month=1, day=1)
        else:
            start_date = current_date.replace(day=1)
        
        expenses = Expense.objects.filter(
            user=user,
            date__gte=start_date.date()
        )
        
        total_in_target = Decimal(0)
        for expense in expenses:
            converted = convert_currency(expense.amount, expense.currency, target_currency)
            total_in_target += converted
        
        return JsonResponse({
            'total': str(total_in_target),
            'currency': target_currency,
            'period': period,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
