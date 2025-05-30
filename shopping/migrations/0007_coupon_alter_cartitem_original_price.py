# Generated by Django 5.2 on 2025-05-10 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0006_add_saved_for_later'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('discount_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('max_discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('min_purchase_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('usage_limit', models.IntegerField(default=1)),
                ('used_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='original_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
