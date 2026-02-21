# Currency Conversion Feature Guide

## Overview
Your expense tracker now supports multi-currency expenses with real-time currency conversion capabilities.

## Features

### 1. **Multi-Currency Expense Tracking**
- Add expenses in 10 different currencies:
  - USD (US Dollar)
  - EUR (Euro)
  - GBP (British Pound)
  - INR (Indian Rupee)
  - JPY (Japanese Yen)
  - AUD (Australian Dollar)
  - CAD (Canadian Dollar)
  - CHF (Swiss Franc)
  - CNY (Chinese Yuan)
  - SEK (Swedish Krona)

### 2. **Expense Form Enhancement**
The expense form now includes a currency field where you can select the currency for each expense:
```
Amount: [input field]
Currency: [dropdown - select from 10 currencies]
Category: [dropdown]
Date: [date picker]
Description: [text area]
Mood: [dropdown]
```

### 3. **Conversion Utilities**
#### Convert Amount
Convert any amount from one currency to another:
```python
from tracker.utils import convert_currency
from decimal import Decimal

# Example: Convert $100 USD to EUR
amount_in_eur = convert_currency(Decimal('100'), 'USD', 'EUR')
# Result: Decimal('92.00')
```

#### Expense Method
Convert a stored expense to any currency:
```python
expense = Expense.objects.first()
amount_in_eur = expense.get_amount_in_currency('EUR')
```

### 4. **API Endpoints**

#### Convert Currency API
**POST** `/tracker/api/convert-currency/`

Convert an amount from one currency to another.

Request:
```json
{
  "amount": "100",
  "from_currency": "USD",
  "to_currency": "EUR"
}
```

Response:
```json
{
  "original_amount": "100",
  "from_currency": "USD",
  "to_currency": "EUR",
  "converted_amount": "92.00"
}
```

#### Get Supported Currencies
**GET** `/tracker/api/supported-currencies/`

Get list of all supported currencies.

Response:
```json
{
  "currencies": ["USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK"]
}
```

#### Get Expense Total in Currency
**GET** `/tracker/api/expense-total-in-currency/?currency=EUR&period=month`

Get total expenses converted to a specific currency.

Parameters:
- `currency`: Target currency code (default: USD)
- `period`: Time period - 'week', 'month', 'year' (default: month)

Response:
```json
{
  "total": "945.50",
  "currency": "EUR",
  "period": "month"
}
```

## Exchange Rates

The conversion uses fixed exchange rates (as of February 2026):

| Currency | Rate (to USD) |
|----------|---------------|
| USD | 1.0 |
| EUR | 0.92 |
| GBP | 0.79 |
| INR | 83.12 |
| JPY | 149.50 |
| AUD | 1.55 |
| CAD | 1.37 |
| CHF | 0.88 |
| CNY | 7.24 |
| SEK | 10.85 |

**Note:** These are fixed rates for consistency. For production use with live rates, you can integrate with services like:
- OpenExchangeRates API
- Fixer.io
- OANDA API
- Currencylayer

## Usage Examples

### 1. Add Expense in Foreign Currency
Go to `/tracker/expense/add/` and:
1. Enter the amount (e.g., 50)
2. Select currency (e.g., EUR)
3. Select category
4. Set date and mood
5. Submit

### 2. View Expenses in Different Currency
```javascript
// Frontend JavaScript example
fetch('/tracker/api/expense-total-in-currency/?currency=EUR&period=month')
  .then(response => response.json())
  .then(data => {
    console.log(`Total: ${data.total} ${data.currency}`);
  });
```

### 3. Backend Conversion
```python
from tracker.models import Expense
from tracker.utils import convert_currency
from decimal import Decimal

# Get all expenses and sum them in EUR
total_eur = Decimal(0)
for expense in Expense.objects.filter(user=request.user):
    total_eur += expense.get_amount_in_currency('EUR')

print(f"Total: €{total_eur}")
```

## Database Changes

A new field has been added to the `Expense` model:
- **currency** (CharField, max_length=3, default='USD')

This field stores the original currency of each expense, allowing accurate tracking of multi-currency transactions.

## CSV Export

When exporting expenses to CSV, the currency column is now included:
```
Date,Category,Amount,Currency,Description,Mood
2024-01-15,Food,50.00,EUR,Dinner in Paris,happy
2024-01-16,Transport,100.00,USD,Flight ticket,neutral
```

## Future Enhancements

Potential improvements:
1. **Live Exchange Rates**: Integrate with external API for real-time rates
2. **Default User Currency**: Allow users to set their preferred base currency
3. **Currency Conversion History**: Track exchange rates over time
4. **Bulk Conversion**: Convert all expenses to a single currency for reporting
5. **Currency-Aware Budgets**: Set budgets in different currencies
6. **Historical Rates**: Use historical rates for expenses in the past

## Troubleshooting

### Issue: Currency field not showing in form
- Solution: Clear browser cache and restart the development server
- Ensure migration was applied: `python manage.py migrate`

### Issue: Conversion API returns error
- Check that both currencies are in the supported list
- Ensure amount is a valid decimal number
- Verify user is authenticated

### Issue: Expenses not converting correctly
- Verify the expense has a valid currency code
- Check that currency is in the CURRENCY_CHOICES in models.py
- Ensure rates in utils.py are up-to-date

## Support

For issues or feature requests related to currency conversion, check:
1. [Django Documentation](https://docs.djangoproject.com/)
2. [Python Decimal Module](https://docs.python.org/3/library/decimal.html)
3. Exchange rate provider documentation if integrating live rates
