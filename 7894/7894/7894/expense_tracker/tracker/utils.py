from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import statistics

from .models import (
    Expense, SpendingPersonality, MoodAnalysis, MoneyLeak,
    BurnRatePrediction, MonthlyStory, Budget, Category, BankAccount, Transaction
)
import random
import uuid


# =============================
# CURRENCY CONVERSION
# =============================

CURRENCY_RATES = {
    'USD': 1.0,
    'EUR': 0.92,
    'GBP': 0.79,
    'INR': 83.12,
    'JPY': 149.50,
    'AUD': 1.55,
    'CAD': 1.37,
    'CHF': 0.88,
    'CNY': 7.24,
    'SEK': 10.85,
}

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'INR': '₹',
    'JPY': '¥',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'CHF',
    'CNY': '¥',
    'SEK': 'kr',
}

def get_currency_symbol(currency_code):
    return CURRENCY_SYMBOLS.get(currency_code, currency_code)


def convert_currency(amount, from_currency, to_currency):
    """
    Convert amount from one currency to another.
    Uses cached rates for performance.
    
    Args:
        amount: Decimal amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'EUR')
    
    Returns:
        Decimal: Converted amount rounded to 2 decimal places
    """
    if from_currency == to_currency:
        return Decimal(str(amount))
    
    from_rate = CURRENCY_RATES.get(from_currency, 1.0)
    to_rate = CURRENCY_RATES.get(to_currency, 1.0)
    
    if from_rate == 0 or to_rate == 0:
        raise ValueError(f"Unsupported currency: {from_currency} or {to_currency}")
    
    # Convert to base (USD) then to target
    in_usd = Decimal(str(amount)) / Decimal(str(from_rate))
    converted = in_usd * Decimal(str(to_rate))
    
    return Decimal(str(converted)).quantize(Decimal('0.01'))


def get_supported_currencies():
    """Return list of supported currencies."""
    return list(CURRENCY_RATES.keys())


def analyze_spending_personality(user):
    """Analyze user's spending personality based on spending patterns."""
    
    # Get last 3 months of expenses
    three_months_ago = timezone.now() - timedelta(days=90)
    expenses = Expense.objects.filter(user=user, date__gte=three_months_ago.date())
    
    if expenses.count() < 5:
        return None
    
    # Calculate metrics
    # Calculate metrics with currency conversion
    try:
        budget = Budget.objects.get(user=user)
        target_currency = budget.currency
    except Budget.DoesNotExist:
        target_currency = 'USD'
        
    amounts = []
    weekend_spending = Decimal(0)
    weekday_spending = Decimal(0)
    
    for expense in expenses:
        converted = convert_currency(expense.amount, expense.currency, target_currency)
        amounts.append(converted)
        
        # Python weekday: 0=Mon, 4=Fri, 5=Sat, 6=Sun
        if expense.date.weekday() >= 5:
            weekend_spending += converted
        else:
            weekday_spending += converted
    
    # Variance score (0-100): high variance = impulse spender
    if len(amounts) > 1:
        variance = statistics.variance(amounts)
        std_dev = statistics.stdev(amounts)
        mean = statistics.mean(amounts)
        variance_score = min(100, (std_dev / mean * 100)) if mean > 0 else 0
    else:
        variance_score = 0
    
    # Category diversity (0-100)
    unique_categories = expenses.values('category').distinct().count()
    total_categories = 10  # Approximate max categories
    category_diversity = (unique_categories / total_categories) * 100
    
    if weekday_spending > 0:
        weekend_vs_weekday_ratio = float(weekend_spending) / float(weekday_spending)
    else:
        weekend_vs_weekday_ratio = 0
    
    # Determine personality
    if variance_score > 60:
        personality_type = 'impulse_spender'
    elif category_diversity < 30:
        personality_type = 'minimalist'
    elif variance_score < 30:
        personality_type = 'planner'
    else:
        personality_type = 'balanced'
    
    # Confidence score based on data points
    confidence = min(100, (expenses.count() / 50) * 100)
    
    personality, created = SpendingPersonality.objects.update_or_create(
        user=user,
        defaults={
            'personality_type': personality_type,
            'variance_score': variance_score,
            'category_diversity': category_diversity,
            'weekend_vs_weekday_ratio': weekend_vs_weekday_ratio,
            'confidence_score': confidence,
        }
    )
    
    return personality


def analyze_mood_patterns(user):
    """Analyze emotional spending patterns."""
    
    current_month = timezone.now()
    month_start = current_month.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    expenses = Expense.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lte=month_end.date()
    )
    
    mood_analyses = []
    
    for mood in ['happy', 'neutral', 'stressed']:
        mood_expenses = expenses.filter(mood=mood)
        
        if mood_expenses.exists():
            # By category
            for category in mood_expenses.values('category').distinct():
                cat_expenses = mood_expenses.filter(category=category['category'])
                
                # Calculate totals with currency conversion
                try:
                    budget = Budget.objects.get(user=user)
                    target_currency = budget.currency
                except Budget.DoesNotExist:
                    target_currency = 'USD'
                
                total_spent = Decimal(0)
                count = 0
                for expense in cat_expenses:
                    total_spent += convert_currency(expense.amount, expense.currency, target_currency)
                    count += 1
                
                avg_amount = total_spent / count if count > 0 else 0
                
                analysis, created = MoodAnalysis.objects.update_or_create(
                    user=user,
                    mood=mood,
                    category=category['category'],
                    period='monthly',
                    defaults={
                        'average_amount': avg_amount,
                        'frequency': count,
                        'total_spent': total_spent,
                    }
                )
                mood_analyses.append(analysis)
    
    return mood_analyses


def detect_money_leaks(user, month):
    """Detect small but frequent expenses that accumulate."""
    
    month_start = month
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    expenses = Expense.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lte=month_end.date()
    )
    
    
    leaks = []
    
    # Detect categories with many small transactions
    # Must use empty order_by() to clear Meta ordering for distinct() to work properly
    for category_data in expenses.order_by().values('category__name').distinct():
        cat_name = category_data['category__name']
        cat_expenses = expenses.filter(category__name=cat_name)
        
        try:
            budget = Budget.objects.get(user=user)
            target_currency = budget.currency
            threshold_amount = budget.leak_threshold
        except Budget.DoesNotExist:
            target_currency = 'USD'
            threshold_amount = Decimal(5)
            
        # Check for low-value transactions with conversion
        small_transactions_count = 0
        total_small = Decimal(0)
        leak_transactions = []
        
        for expense in cat_expenses:
            converted = convert_currency(expense.amount, expense.currency, target_currency)
            if converted <= threshold_amount:
                small_transactions_count += 1
                total_small += converted
                leak_transactions.append(expense)
        
        if small_transactions_count >= 1:  # Group any category with at least one small transaction
            total = total_small
            avg = total / small_transactions_count if small_transactions_count > 0 else 0
            count = small_transactions_count
            
            frequency = f"{count} times"
            if count >= 20:
                frequency = f"{count // 30} times per day"
            
            severity = 'low' if total < 50 else 'medium' if total < 100 else 'high'
            
            leak, created = MoneyLeak.objects.update_or_create(
                user=user,
                category=cat_name,
                month=month_start,
                defaults={
                    'monthly_total': total_small,
                    'transaction_count': count,
                    'average_transaction': avg,
                    'frequency_description': frequency,
                    'severity': severity,
                }
            )
            # monkey-patch transactions for template display (not saved to DB)
            leak.transactions = leak_transactions
            leaks.append(leak)
    
    return leaks


def predict_burn_rate(user):
    """Predict end-of-month spending based on current daily averages."""
    
    current_month = timezone.now()
    month_start = current_month.replace(day=1)
    today = current_month.date()
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get expenses so far this month
    expenses_so_far = Expense.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lte=today
    )
    
    # Calculate total with currency conversion
    try:
        budget = Budget.objects.get(user=user)
        target_currency = budget.currency
    except Budget.DoesNotExist:
        target_currency = 'USD'
        
    total_so_far = Decimal(0)
    for expense in expenses_so_far:
        total_so_far += convert_currency(expense.amount, expense.currency, target_currency)
    days_passed = (today - month_start.date()).days + 1
    
    # Calculate daily average
    if days_passed > 0:
        daily_average = total_so_far / days_passed
    else:
        daily_average = Decimal(0)
    
    # Project to end of month
    days_in_month = (month_end.date() - month_start.date()).days + 1
    projected_total = daily_average * days_in_month
    
    # Get budget
    budget = Budget.objects.get(user=user)
    
    # Calculate predictions
    will_overspend = projected_total > budget.monthly_budget
    
    if budget.monthly_budget > 0:
        overspend_percentage = max(0, float((projected_total - budget.monthly_budget) / budget.monthly_budget * 100))
        savings_percentage = max(0, float((budget.monthly_budget - projected_total) / budget.monthly_budget * 100))
    else:
        overspend_percentage = 0
        savings_percentage = 0
    
    # Estimate exhaustion date
    if daily_average > 0:
        days_until_exhaustion = float(budget.monthly_budget / daily_average)
        exhaustion_date = month_start.date() + timedelta(days=days_until_exhaustion)
        if exhaustion_date > month_end.date():
            exhaustion_date = None
    else:
        exhaustion_date = None
    
    prediction, created = BurnRatePrediction.objects.update_or_create(
        user=user,
        current_month=month_start.date(),
        defaults={
            'daily_average_spend': daily_average,
            'projected_month_total': projected_total,
            'budget_amount': budget.monthly_budget,
            'estimated_exhaustion_date': exhaustion_date,
            'will_overspend': will_overspend,
            'overspend_percentage': overspend_percentage,
            'savings_percentage': savings_percentage,
        }
    )
    
    return prediction


def generate_monthly_story(user, month):
    """Generate a narrative-style monthly summary."""
    
    month_start = month
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    expenses = Expense.objects.filter(
        user=user,
        date__gte=month_start,
        date__lte=month_end
    )
    
    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    # Top spending category
    top_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total').first()
    
    # Budget comparison
    budget = Budget.objects.get(user=user)
    budget_vs_actual = ""
    if budget.monthly_budget > 0:
        diff = budget.monthly_budget - total_spent
        if diff > 0:
            budget_vs_actual = f"{diff:.2f} under budget"
        else:
            budget_vs_actual = f"{abs(diff):.2f} over budget"
    
    # Emotional trends
    stressed_expenses = expenses.filter(mood='stressed').aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    happy_expenses = expenses.filter(mood='happy').aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    
    emotional_trend = "Balanced spending"
    if stressed_expenses > total_spent * Decimal('0.4'):
        emotional_trend = "Stress-related spending detected"
    elif happy_expenses > total_spent * Decimal('0.4'):
        emotional_trend = "Happy spending mood detected"
    
    # Money leaks
    leaks = MoneyLeak.objects.filter(user=user, month=month_start)
    leak_alerts = [
        {
            'category': leak.category,
            'amount': str(leak.monthly_total),
            'frequency': leak.frequency_description
        }
        for leak in leaks
    ]
    
    # Generate narrative
    top_category_name = top_category.get('category', 'N/A') if top_category else 'N/A'
    top_category_amount = top_category.get('total', 0) if top_category else 0
    
    narrative = f"""
    This month, you spent a total of ${total_spent:.2f}. Your top spending category was {top_category_name} 
    with ${top_category_amount:.2f} in expenses. You are {budget_vs_actual}. 
    
    Emotionally, {emotional_trend.lower()}. This is a good time to reflect on your spending patterns and adjust your budget if needed.
    """
    
    if leak_alerts:
        narrative += f"\n\nWe detected {len(leak_alerts)} money leaks this month. Consider reviewing these small frequent purchases."
    
    # Key insights
    key_insights = [
        f"Top category: {top_category_name} (${top_category_amount:.2f})",
        f"Total expenses: ${total_spent:.2f}",
        f"Budget status: {budget_vs_actual}",
        f"Emotional trend: {emotional_trend}",
    ]
    
    story, created = MonthlyStory.objects.update_or_create(
        user=user,
        month=month_start,
        defaults={
            'narrative': narrative.strip(),
            'top_category': top_category.get('category', '') if top_category else '',
            'top_category_amount': top_category.get('total', 0) if top_category else 0,
            'total_spent': total_spent,
            'budget_vs_actual': budget_vs_actual,
            'emotional_trend': emotional_trend,
            'money_leak_alerts': leak_alerts,
            'key_insights': key_insights,
        }
    )
    
    return story


# =============================
# BANK SYNC & MOCK TRANSACTIONS
# =============================

MOCK_MERCHANTS = {
    'Food': ['Swiggy', 'Zomato', 'Dominos', 'McDonalds', 'Starbucks', 'KFC', 'Burger King', 'Subway'],
    'Groceries': ['BigBasket', 'Blinkit', 'Zepto', 'DMart', 'Local Kirana', 'Reliance Fresh'],
    'Shopping': ['Amazon', 'Flipkart', 'Myntra', 'Ajio', 'H&M', 'Zara', 'Uniqlo', 'Decathlon'],
    'Transport': ['Uber', 'Ola', 'Rapido', 'Metro Card', 'Shell Fuel', 'Indian Oil'],
    'Utilities': ['Electricity Board', 'Gas Bill', 'Water Bill', 'Jio Fiber', 'Airtel Broadband'],
    'Entertainment': ['Netflix', 'Spotify', 'BookMyShow', 'PVR Cinemas', 'Steam Games', 'PlayStation'],
    'Healthcare': ['Apollo Pharmacy', 'Practo', 'Dr. Lal PathLabs', 'Netmeds', '1mg'],
    'Travel': ['MakeMyTrip', 'Goibibo', 'IRCTC', 'Indigo', 'Air India', 'Oyo Rooms'],
    'Education': ['Udemy', 'Coursera', 'Kindle Books', 'College Fees', 'Stationery Shop'],
    'Other': ['ATM Withdrawal', 'Bank Charges', 'Gift Shop', 'Donation', 'Pet Shop'],
}

# Mapping from expanded mock categories to actual database categories
CATEGORY_MAPPING = {
    'Food': 'Food',
    'Groceries': 'Food',
    'Shopping': 'Shopping',
    'Transport': 'Travel',
    'Utilities': 'Utilities',
    'Entertainment': 'Entertainment',
    'Healthcare': 'Other',
    'Travel': 'Travel',
    'Education': 'Other',
    'Other': 'Other',
    'Rent': 'Rent',
}

def auto_categorize(merchant_name, description):
    """Smart categorization based on merchant name and keywords."""
    
    # 1. Direct Keyword Match from DB
    categories = Category.objects.all()
    for category in categories:
        if category.keywords:
            keywords = [k.strip().lower() for k in category.keywords.split(',')]
            text_to_search = (merchant_name + " " + description).lower()
            for keyword in keywords:
                if keyword in text_to_search:
                    return category

    # 2. Mock Merchant Mapping
    text_to_search = (merchant_name + " " + description).lower()
    for mock_cat, merchants in MOCK_MERCHANTS.items():
        for merchant in merchants:
            if merchant.lower() in text_to_search:
                target_cat_name = CATEGORY_MAPPING.get(mock_cat, 'Other')
                category = Category.objects.filter(name__iexact=target_cat_name).first()
                if category:
                    return category
                
    # 3. Default Fallback
    fallback = Category.objects.filter(name__in=['Other', 'Unknown', 'Uncategorized']).first()
    return fallback


def generate_mock_transactions(account, count=35):
    """Generate realistic mock transactions for a bank account."""
    
    transactions = []
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=60) # Last 2 months
    
    for _ in range(count):
        # Pick random category and merchant
        cat_name = random.choice(list(MOCK_MERCHANTS.keys()))
        merchant = random.choice(MOCK_MERCHANTS[cat_name])
        
        # Pick random date
        random_days = random.randint(0, 60)
        txn_date = end_date - timedelta(days=random_days)
        
        # Random amount based on category
        if cat_name in ['Food', 'Transport']:
            amount = random.uniform(50, 500)
        elif cat_name in ['Groceries', 'Shopping', 'Entertainment']:
            amount = random.uniform(500, 5000)
        elif cat_name in ['Travel', 'Healthcare']:
            amount = random.uniform(1000, 15000)
        else:
            amount = random.uniform(100, 2000)
            
        currency = account.currency
        
        # Transaction Type (90% debit, 10% credit)
        if random.random() < 0.9:
            txn_type = 'debit'
            description = f"Purchase from {merchant}"
        else:
            txn_type = 'credit'
            merchant = "Refund / Transfer" # Override merchant
            description = "Credit adjustment or Refund"
            cat_name = 'Other'
            amount = random.uniform(100, 5000)

        # Create Transaction Object
        txn = Transaction(
            account=account,
            transaction_id=str(uuid.uuid4()),
            date=txn_date,
            amount=Decimal(amount).quantize(Decimal('0.01')),
            currency=currency,
            description=description,
            merchant_name=merchant,
            transaction_type=txn_type,
            # We will categorize it later during sync
        )
        transactions.append(txn)
    
    # Bulk create for efficiency
    Transaction.objects.bulk_create(transactions)
    
    return transactions


def sync_bank_account(account_id):
    """
    Syncs transactions for a bank account.
    1. Fetches new transactions (mock data for now).
    2. Auto-categorizes them.
    3. Creates corresponding Expense entries.
    """
    try:
        account = BankAccount.objects.get(id=account_id)
        
        # In a real app, this would fetch from an API like Plaid/Yodlee
        # Here we just check if it's the first sync or forced sync
        
        # If no transactions exist, generate initial mock data
        if not account.transactions.exists():
            new_transactions = generate_mock_transactions(account, count=40)
        else:
            # Generate a few new random transactions to simulate real-time updates
            new_transactions = generate_mock_transactions(account, count=random.randint(2, 5))
            
        # Process transactions
        synced_count = 0
        for txn in new_transactions: # These are already saved by generate_mock_transactions logic above? 
                                     # Wait, bulk_create saves them. So we iterate over saved instances
                                     
            # 1. Auto Categorize
            category = auto_categorize(txn.merchant_name, txn.description)
            txn.category = category
            txn.save()

            # 2. Create Expense if it's a Debit
            if txn.transaction_type == 'debit':
                expense_description = f"{txn.merchant_name} ({txn.description})"
                
                expense = Expense.objects.create(
                    user=account.user,
                    amount=txn.amount,
                    currency=txn.currency,
                    category=category if category else Category.objects.get_or_create(name='Uncategorized')[0],
                    date=txn.date.date(),
                    description=expense_description,
                    mood='neutral' # Default mood
                )
                
                # Link expense to transaction
                txn.expense = expense
                txn.save()
                
            synced_count += 1
            
        # Update last synced timestamp
        account.last_synced = timezone.now()
        account.save()
        
        return synced_count

    except BankAccount.DoesNotExist:
        return 0

