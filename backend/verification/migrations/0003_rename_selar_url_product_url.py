from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0002_campaign_alter_assignedcoupon_coupon_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='campaign',
            old_name='selar_url',
            new_name='product_url',
        ),
    ]
