# Generated by Django 5.1.1 on 2024-09-27 19:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_order_shipping_address_alter_order_total_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='quiantity',
            new_name='quantity',
        ),
    ]
