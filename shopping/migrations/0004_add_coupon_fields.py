from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0003_auto_20250510_0631'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='coupon_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cart',
            name='coupon_discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ] 