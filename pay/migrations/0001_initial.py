import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

from pay import app_settings
from pay import constants


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PayCard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cardnumber_ending', models.CharField(blank=True, max_length=4, verbose_name='Card number (last 4 digits)')),
                ('holder', models.CharField(blank=True, max_length=75, verbose_name='Card holder’s name')),
                ('address', models.CharField(blank=True, max_length=150, verbose_name='Billing address')),
                ('postcode', models.CharField(blank=True, max_length=15, verbose_name='Billing postcode')),
                ('expire_month', models.IntegerField(blank=True, choices=constants.MONTH_CHOICES, null=True, verbose_name='Expiration month')),
                ('expire_year', models.IntegerField(blank=True, choices=constants.YEAR_CHOICES, null=True, verbose_name='Expiration year')),
                ('created_at', models.DateTimeField(default=datetime.datetime.now, editable=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(blank=True, choices=app_settings.PAY_PAYMENT_METHODS, default='cc', max_length=2, verbose_name='Payment Method')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('currency', models.CharField(choices=app_settings.PAY_CURRENCIES, default='GBP', max_length=3)),
                ('complete', models.BooleanField(default=False, verbose_name='Complete')),
                ('time_stamp', models.DateTimeField(default=datetime.datetime.now, editable=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('plan', models.IntegerField(blank=True, choices=app_settings.PAY_PLAN_CHOICES, default=0, null=True, verbose_name='Plan')),
                ('expires', models.DateTimeField(blank=True, null=True, verbose_name='active until')),
                ('recurring', models.BooleanField(default=False, verbose_name='Auto-renew')),
                ('updated_at', models.DateTimeField(default=datetime.datetime.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='CardNumber',
            fields=[
                ('paycard', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='pay.paycard')),
                ('encrypted', models.CharField(blank=True, editable=False, max_length=40, verbose_name='Encrypted PAN')),
            ],
        ),
        migrations.CreateModel(
            name='CVV',
            fields=[
                ('paycard', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='pay.paycard')),
                ('encrypted', models.CharField(blank=True, editable=False, max_length=40, verbose_name='Encrypted CVV')),
            ],
        ),
        migrations.CreateModel(
            name='CardReceipt',
            fields=[
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='pay.payment')),
                ('details', models.CharField(blank=True, max_length=255)),
                ('authcode', models.CharField(blank=True, max_length=20)),
                ('reference', models.CharField(blank=True, max_length=20)),
                ('reason_code', models.CharField(blank=True, max_length=20)),
                ('avs_address', models.CharField(blank=True, choices=constants.AVS_RESPONSES, max_length=1, verbose_name='AVS address check')),
                ('avs_postcode', models.CharField(blank=True, choices=constants.AVS_RESPONSES, max_length=1, verbose_name='AVS postcode check')),
                ('paycard', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pay.paycard')),
            ],
        ),
    ]
