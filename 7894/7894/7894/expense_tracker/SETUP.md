# Expense Tracker - Setup Guide

A comprehensive Django-based expense tracking application with advanced analytics including spending personality analysis, mood tracking, money leak detection, burn rate prediction, and interactive what-if simulations.

## Features

### Core Features
- User authentication (signup/login)
- Add, edit, delete, and filter expenses
- Monthly budget tracking
- Category-wise budget management
- Dashboard with interactive charts
- CSV export functionality

### Advanced Analytics
- **Spending Personality Analysis**: Classify users into personality types (Planner, Impulse Spender, Minimalist, Balanced)
- **Mood Tracking**: Analyze emotional spending patterns
- **Money Leak Detector**: Identify small but frequent expenses
- **Burn Rate Prediction**: Predict month-end spending and budget exhaustion
- **What-If Simulator**: Test spending reduction scenarios
- **Monthly Story Mode**: Narrative-style monthly summaries with insights

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Step 1: Clone/Setup Project
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Django
```bash
# Create .env file in project root (optional for development)
# For production, set these as environment variables

# Apply database migrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser

# Collect static files (for production)
python manage.py collectstatic
```

### Step 3: Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Project Structure

```
expense_tracker/
├── expense_tracker/          # Main Django project
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI configuration
│   └── __init__.py
├── tracker/                 # Expense tracker app
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # App URL routing
│   ├── forms.py             # Django forms
│   ├── utils.py             # Utility functions for analytics
│   ├── admin.py             # Django admin configuration
│   └── __init__.py
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── home.html            # Home page
│   ├── dashboard.html       # Main dashboard
│   ├── auth/                # Authentication templates
│   └── tracker/             # App templates
│       ├── expense_*.html
│       ├── budget_*.html
│       ├── insights/        # Insight templates
│       └── simulator/       # Simulator template
├── static/                  # Static files (CSS, JS, images)
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
└── SETUP.md                # This file
```

## Database Models

### Core Models
- **User**: Django's built-in user model
- **Expense**: Individual expense transactions
- **Budget**: Monthly budget for users
- **CategoryBudget**: Category-specific budgets

### Analytics Models
- **SpendingPersonality**: User personality classification
- **MoodAnalysis**: Mood-based spending patterns
- **MoneyLeak**: Detected small frequent expenses
- **BurnRatePrediction**: Month-end spending projection
- **MonthlyStory**: Narrative monthly summaries
- **WhatIfSimulation**: Saved simulation scenarios

## Key Features Explained

### Dashboard
The main hub showing:
- Total spending vs budget
- Budget progress bar
- Spending personality
- Projected month-end spending
- Category breakdown pie chart
- Daily spending trend line chart
- Recent expenses

### Expense Management
- Add expenses with amount, category, date, description, and mood
- Filter by category, mood, date range, amount
- Edit or delete existing expenses
- View all expenses in a table format

### Spending Personality
Based on:
- Variance in spending amounts
- Diversity of spending categories
- Weekend vs weekday spending patterns
- Confidence score based on data points

### Mood Analysis
- Tag expenses with mood (Happy, Neutral, Stressed)
- View spending by mood and category
- Identify emotional spending triggers

### Money Leak Detector
Finds categories with:
- 5+ small transactions (under $5)
- Total accumulated spending
- Frequency and severity classification
- Actionable recommendations

### Burn Rate Prediction
Shows:
- Daily average spending
- Projected month-end total
- Budget exhaustion date (if applicable)
- Savings/overspend percentage
- Recommendations for course correction

### What-If Simulator
- Interactive sliders for each category
- Real-time savings calculation
- Quick presets (10%, 25%, 50% reduction)
- Visual feedback on impact

### Monthly Story
Narrative summary including:
- Total spending analysis
- Top spending categories
- Budget performance
- Emotional trends
- Money leak alerts
- Key insights and recommendations

## Usage

### Basic Workflow
1. **Sign Up**: Create an account
2. **Set Budget**: Configure monthly budget
3. **Add Expenses**: Log daily expenses with categories and moods
4. **View Dashboard**: Monitor spending and budget progress
5. **Explore Insights**: 
   - Check personality analysis
   - Review mood patterns
   - Identify money leaks
   - Check burn rate prediction
6. **Plan**: Use what-if simulator to test spending scenarios
7. **Reflect**: Read monthly story for insights

### Admin Panel
Access at `/admin/` with superuser credentials to:
- Manage users
- View and edit expenses
- Monitor analytics models
- Export data

## API Endpoints

### Data APIs
- `GET /tracker/api/expense-data/` - Get expense data by period
- `GET /tracker/api/chart-data/` - Get chart-ready data
- `POST /tracker/api/simulator/` - Calculate simulation results

### Export
- `GET /tracker/export/csv/` - Export all expenses as CSV

## Settings Reference

Key settings in `expense_tracker/settings.py`:
- `EXPENSE_CATEGORIES`: Define available categories
- `MOOD_CHOICES`: Define mood options
- `SPENDING_PERSONALITIES`: Personality type configurations

## Deployment

### Production Checklist
1. Set `DEBUG = False` in settings.py
2. Set secure `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use environment variables for sensitive data
5. Use PostgreSQL (or other production DB) instead of SQLite
6. Collect static files: `python manage.py collectstatic`
7. Set up HTTPS/SSL
8. Configure email backend for notifications (optional)

### Deploying to Heroku
```bash
# Install Heroku CLI and login
heroku login

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate
```

## Troubleshooting

### Database Issues
```bash
# Reset database (development only)
python manage.py flush
python manage.py migrate

# Recreate indexes
python manage.py shell
>>> from tracker.models import Expense
>>> # Indexes are created automatically on migrate
```

### Static Files Not Loading
```bash
python manage.py collectstatic --no-input
```

### Chart.js Not Rendering
- Ensure Chart.js CDN is accessible
- Check browser console for JavaScript errors
- Verify data is being fetched from API endpoints

## Contributing

To extend the application:

1. **Add New Models**: Update `tracker/models.py`
2. **Create Views**: Add functions to `tracker/views.py`
3. **Update URLs**: Add routes to `tracker/urls.py`
4. **Create Templates**: Add HTML files in `templates/`
5. **Add Analytics**: Extend utility functions in `tracker/utils.py`

## Security Notes

- Passwords are hashed with Django's default PBKDF2
- CSRF protection enabled on all forms
- SQL injection protected via Django ORM
- XSS protection via template auto-escaping
- Always use HTTPS in production

## License

This project is open source and available for educational and personal use.

## Support

For issues or questions:
1. Check this setup guide
2. Review Django documentation
3. Inspect browser console for errors
4. Check Django logs for backend errors

## Future Enhancements

Potential features for future versions:
- Recurring expense automation
- Budget alerts and notifications
- Expense categorization with ML
- Investment tracking
- Savings goals
- Multi-user household budgets
- Mobile app
- Data visualization improvements
- Recurring transaction templates
