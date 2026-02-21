import os
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from groq import Groq
from tracker.models import Expense, Budget, BankAccount, Category
from tracker.utils import convert_currency
import traceback

try:
    client = Groq(api_key=settings.GROQ_API_KEY)
except Exception as e:
    client = None
    print(f"Error initializing Groq client: {e}")

# ==========================================
# TOOL IMPLEMENTATIONS (BACKEND LOGIC)
# ==========================================

def add_expense_tool(user, amount, category_name, description="", date=None, mood='neutral'):
    """Backend logic to add an expense via AI."""
    try:
        category_name = category_name.strip().title()
        category, _ = Category.objects.get_or_create(name=category_name)
        
        expense = Expense.objects.create(
            user=user,
            amount=Decimal(str(amount)),
            category=category,
            description=description or f"Added via AI",
            date=date if date else timezone.now().date(),
            mood=mood
        )
        return {"status": "success", "message": f"Recorded spending of {amount} in {category_name}.", "id": expense.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def update_budget_tool(user, amount, currency='USD'):
    """Backend logic to update budget limit."""
    try:
        budget, created = Budget.objects.update_or_create(
            user=user,
            defaults={'monthly_budget': Decimal(str(amount)), 'currency': currency.upper()}
        )
        return {"status": "success", "message": f"Monthly budget set to {currency.upper()} {amount}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def update_leak_threshold_tool(user, amount):
    """Backend logic to update money leak detection threshold."""
    try:
        budget, created = Budget.objects.get_or_create(user=user)
        budget.leak_threshold = Decimal(str(amount))
        budget.save()
        return {"status": "success", "message": f"Money leak threshold updated to {amount} {budget.currency}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_spending_summary_tool(user, category_name=None, days=30):
    """Get total spending for a category or overall."""
    try:
        days = int(days)
        start_date = timezone.now().date() - timedelta(days=days)
        queryset = Expense.objects.filter(user=user, date__gte=start_date)
        
        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)
            
        total = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Check for uncategorized in this period
        uncat_count = queryset.filter(category__name__iexact='Uncategorized').count()
        
        return {
            "category": category_name or "All",
            "total_spent": str(total),
            "period": f"Last {days} days",
            "transaction_count": queryset.count(),
            "uncategorized_count": uncat_count,
            "suggestion": "I found some uncategorized expenses. Ask me to 'categorize my spending' to sort them!" if uncat_count > 0 else None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_recent_expenses_tool(user, limit=5):
    """Retrieve recent expenses for the user."""
    try:
        limit = int(limit)
        expenses = Expense.objects.filter(user=user).order_by('-date', '-created_at')[:limit]
        data = []
        for e in expenses:
            data.append({
                "amount": str(e.amount),
                "category": e.category.name,
                "description": e.description,
                "date": str(e.date)
            })
        return {"expenses": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def what_if_tool(user, reduction_percentage=20):
    """Calculate expenses if they were reduced by a certain percentage."""
    try:
        reduction = Decimal(str(reduction_percentage)) / 100
        current_month = timezone.now().replace(day=1)
        expenses = Expense.objects.filter(user=user, date__gte=current_month)
        
        total_original = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        total_simulated = total_original * (1 - reduction)
        savings = total_original - total_simulated
        
        return {
            "original_total": str(total_original),
            "simulated_total": str(total_simulated.quantize(Decimal('0.01'))),
            "savings": str(savings.quantize(Decimal('0.01'))),
            "reduction_percentage": f"{reduction_percentage}%"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_burn_rate_tool(user):
    """Predict end-of-month spending and burn rate."""
    try:
        from tracker.utils import predict_burn_rate
        prediction = predict_burn_rate(user)
        return {
            "daily_average": str(prediction.daily_average_spend),
            "projected_total": str(prediction.projected_month_total),
            "budget": str(prediction.budget_amount),
            "will_overspend": prediction.will_overspend,
            "exhaustion_date": str(prediction.estimated_exhaustion_date) if prediction.estimated_exhaustion_date else "Safe",
            "overspend_percentage": f"{prediction.overspend_percentage}%",
            "savings_percentage": f"{prediction.savings_percentage}%"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_personality_tool(user):
    """Analyze the user's spending personality."""
    try:
        from tracker.utils import analyze_spending_personality
        p = analyze_spending_personality(user)
        if not p:
            return {"status": "info", "message": "Not enough data yet (minimum 5 expenses)."}
        return {
            "type": p.personality_type,
            "variance_score": p.variance_score,
            "diversity": p.category_diversity,
            "confidence": p.confidence_score
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_mood_analysis_tool(user):
    """Get insights on how mood affects spending."""
    try:
        from tracker.utils import analyze_mood_patterns
        analyses = analyze_mood_patterns(user)
        data = []
        for a in analyses:
            data.append({
                "mood": a.mood,
                "category": a.category,
                "avg_amount": str(a.average_amount),
                "frequency": a.frequency,
                "total": str(a.total_spent)
            })
        return {"mood_insights": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_money_leaks_tool(user):
    """Detect recurring small expenses (money leaks)."""
    try:
        from tracker.utils import detect_money_leaks
        month = timezone.now().replace(day=1)
        leaks = detect_money_leaks(user, month)
        data = []
        for l in leaks:
            data.append({
                "category": l.category,
                "total": str(l.monthly_total),
                "count": l.transaction_count,
                "frequency": l.frequency_description,
                "severity": l.severity
            })
        return {"leaks": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_monthly_story_tool(user):
    """Get a narrative summary of the current month's finances."""
    try:
        from tracker.utils import generate_monthly_story
        month = timezone.now().replace(day=1).date()
        story = generate_monthly_story(user, month)
        return {
            "narrative": story.narrative,
            "top_category": story.top_category,
            "total_spent": str(story.total_spent),
            "status": story.budget_vs_actual,
            "insights": story.key_insights
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def categorize_expenses_tool(user):
    """Scan all expenses and auto-categorize properties that are 'Uncategorized'."""
    try:
        from tracker.utils import auto_categorize
        from tracker.models import Category, Expense
        from django.db.models import Q
        
        uncat_filter = Q(name__iexact='Uncategorized') | Q(name__iexact='Unknown') | Q(name__iexact='Other')
        uncategorized_cats = Category.objects.filter(uncat_filter)
        
        if not uncategorized_cats.exists():
            return {"status": "info", "message": "No 'Uncategorized' categories found. Everything looks sorted!"}
            
        expenses = Expense.objects.filter(user=user, category__in=uncategorized_cats)
        count = 0
        updates = []
        
        for exp in expenses:
            # Try to categorize based on description
            new_cat = auto_categorize("", exp.description)
            if new_cat and (exp.category is None or new_cat.id != exp.category.id):
                # Only update if it moves from an 'Uncategorized' type to a 'Specific' type
                # Check if new_cat is actually a specific category
                if not (new_cat.name.lower() in ['uncategorized', 'unknown', 'other']):
                    exp.category = new_cat
                    exp.save()
                    count += 1
                    updates.append(f"{exp.description} -> {new_cat.name}")
        
        if count > 0:
            return {
                "status": "success",
                "count_updated": count,
                "updates": updates,
                "message": f"I've successfully sorted {count} expenses into their correct categories!"
            }
        else:
            return {
                "status": "info",
                "message": f"I scanned your spending but couldn't find a better match for the {expenses.count()} items in 'Uncategorized' categories. You might need to set their categories manually in the dashboard."
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# TOOL DEFINITIONS (STRICTER)
# ==========================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Log a new expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "category_name": {"type": "string"},
                    "description": {"type": "string"},
                    "mood": {"type": "string"}
                },
                "required": ["amount", "category_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_budget",
            "description": "Set the monthly budget limit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "currency": {"type": "string"}
                },
                "required": ["amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_leak_threshold",
            "description": "Set the threshold amount for detecting money leaks (small frequent expenses).",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"}
                },
                "required": ["amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_summary",
            "description": "Get total spending stats for a specific number of days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_name": {"type": "string"},
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back. Must be an integer."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_expenses",
            "description": "Retrieve a list of the most recent expenses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 5}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "what_if_calculation",
            "description": "Simulate a budget reduction and calculate resulting expenses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reduction_percentage": {
                        "type": "number",
                        "description": "The percentage to reduce expenses by (e.g. 20 for 20%)."
                    }
                },
                "required": ["reduction_percentage"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_burn_rate",
            "description": "Get burn rate, projection, and overspending risk.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_personality",
            "description": "Analyze spending style (Impulse vs Planner).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_mood_insights",
            "description": "Analyze how mood/emotion (Happy/Stressed) affects spending.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_money_leaks",
            "description": "Find small frequent expenses (leaks).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_story",
            "description": "Get a narrative summary and key insights for the month.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "categorize_expenses",
            "description": "Automatically categorize any expenses that are currently 'Uncategorized'.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# ==========================================
# CORE CHAT LOGIC
# ==========================================

def chat_with_ai(user, user_message):
    if not client:
        return "Chat system offline."

    # Fetch rich context
    try:
        budget = Budget.objects.get(user=user)
        budget_str = f"{budget.currency} {budget.monthly_budget}"
        currency = budget.currency
    except:
        budget_str = "Not set"
        currency = "USD"
    
    current_time = timezone.now()
    
    system_prompt = f"""You are Penny, a sophisticated AI financial coach. You have DIRECT ACCESS to the user's financial data through specialized tools.
    
    USER CONTEXT:
    - User: {user.username}
    - Local Time: {current_time.strftime('%Y-%m-%d %H:%M')}
    - Current Budget: {budget_str}
    
    CORE RULES:
    - NEVER say you don't have access to the user's data. Use your tools to fetch it.
    - If a user asks about spending (e.g. "how much spent on utilities"), ALWAYS call 'get_spending_summary' with the category name.
    - If a user mentions "categorize" or "sort" their spending, use 'categorize_expenses'.
    - Be warm, but authoritative about your financial capabilities.
    
    TOOL MAPPING:
    1. BUDGET & SPENDING: 'get_spending_summary', 'get_recent_expenses'.
    2. CATEGORIZATION: 'categorize_expenses'.
    3. PREDICTIONS: 'get_burn_rate'.
    4. PERSONALITY/MOOD/LEAKS: Respectively 'get_spending_personality', 'get_mood_insights', 'get_money_leaks'.
    5. WHAT-IF/INSIGHTS: 'what_if_calculation', 'get_monthly_story'.
    """

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
    
    try:
        # Loop for up to 3 turns to handle tool results
        for _ in range(3):
            completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.5
            )
            
            response_message = completion.choices[0].message
            
            # If tool calls, we must process them and append to history
            assistant_msg = {
                "role": "assistant",
                "content": response_message.content or ""
            }
            if response_message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]
            
            messages.append(assistant_msg)
            
            if not response_message.tool_calls:
                return response_message.content or "I'm here to help!"
            
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                result = {"error": "Tool not found"}
                if fn_name == "add_expense":
                    result = add_expense_tool(user, **fn_args)
                elif fn_name == "update_budget":
                    result = update_budget_tool(user, **fn_args)
                elif fn_name == "update_leak_threshold":
                    result = update_leak_threshold_tool(user, **fn_args)
                elif fn_name == "get_spending_summary":
                    result = get_spending_summary_tool(user, **fn_args)
                elif fn_name == "get_recent_expenses":
                    result = get_recent_expenses_tool(user, **fn_args)
                elif fn_name == "what_if_calculation":
                    result = what_if_tool(user, **fn_args)
                elif fn_name == "get_burn_rate":
                    result = get_burn_rate_tool(user)
                elif fn_name == "get_spending_personality":
                    result = get_personality_tool(user)
                elif fn_name == "get_mood_insights":
                    result = get_mood_analysis_tool(user)
                elif fn_name == "get_money_leaks":
                    result = get_money_leaks_tool(user)
                elif fn_name == "get_monthly_story":
                    result = get_monthly_story_tool(user)
                elif fn_name == "categorize_expenses":
                    result = categorize_expenses_tool(user)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": json.dumps(result)
                })
                
        return messages[-1].get("content") or "I've processed your request!"

    except Exception as e:
        error_msg = str(e)
        print(f"Penny Error: {error_msg}")
        
        with open("penny_errors.log", "a") as f:
            f.write(f"[{timezone.now()}] ERROR: {error_msg}\n")
            import traceback
            f.write(traceback.format_exc())
            f.write("-" * 20 + "\n")
        
        if "rate_limit" in error_msg.lower():
            return "I'm experiencing a bit of a rush right now (Rate Limit). Please wait a few seconds and try again! I'm ready to help with your data."
            
        # Fallback: Try a simple chat without tools if the tool turn failed
        try:
            fallback_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "You are Penny, the user's financial AI. The data connection is temporarily unstable. Assist the user as best as you can, but remind them that sync is preferred."}, {"role": "user", "content": user_message}],
                model="llama-3.1-8b-instant", # Use a smaller model for fallback to save quota
            )
            return fallback_completion.choices[0].message.content
        except:
            return "I ran into a technical snag. Try asking again differently!"
