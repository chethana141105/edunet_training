from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expense/add/', views.add_expense, name='add_expense'),
    path('expense/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    
    # Budget
    path('budget/', views.budget_settings, name='budget_settings'),
    path('budget/category/', views.category_budget_settings, name='category_budget_settings'),
    
    # Bank Accounts
    path('bank-accounts/', views.bank_accounts, name='bank_accounts'),
    path('bank-accounts/link/', views.link_bank_account, name='link_bank_account'),
    path('bank-accounts/<int:pk>/unlink/', views.unlink_bank_account, name='unlink_bank_account'),

    
    # Insights
    path('insights/personality/', views.personality_insights, name='personality_insights'),
    path('insights/mood/', views.mood_insights, name='mood_insights'),
    path('insights/money-leak/', views.money_leak_insights, name='money_leak_insights'),
    path('insights/burn-rate/', views.burn_rate_insights, name='burn_rate_insights'),
    
    # Story Mode
    path('story/monthly/', views.monthly_story, name='monthly_story'),
    
    # Simulator
    path('simulator/what-if/', views.what_if_simulator, name='what_if_simulator'),
    
    # API endpoints (for AJAX/Chart.js)
    path('api/expense-data/', views.expense_data_api, name='expense_data_api'),
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('api/simulator/', views.simulator_api, name='simulator_api'),
    
    # Currency Conversion API
    path('api/convert-currency/', views.convert_currency_api, name='convert_currency_api'),
    path('api/supported-currencies/', views.supported_currencies_api, name='supported_currencies_api'),
    path('api/expense-total-in-currency/', views.expense_total_in_currency, name='expense_total_in_currency'),
    
    # Export
    path('export/csv/', views.export_csv, name='export_csv'),
]
