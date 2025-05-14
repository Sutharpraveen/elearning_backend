from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0004_add_coupon_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='discount_percentage',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ] 