# Generated migration for adding currency field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='currency',
            field=models.CharField(
                choices=[
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
                ],
                default='USD',
                max_length=3,
            ),
        ),
    ]
