from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0005_add_discount_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='is_saved_for_later',
            field=models.BooleanField(default=False),
        ),
    ] 