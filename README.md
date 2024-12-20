# Django-Pay: Payments and Subscriptions Made Easy

[![Build Status](https://travis-ci.org/fmalina/django-pay.svg?branch=main)](https://travis-ci.org/fmalina/django-pay)


**Django-Pay** is a reusable Django app for managing subscriptions, payment cards, and transactions. Designed for seamless integration and PCI compliance, it supports Realex, PayPal, and Global Payments gateways.

## Features

- **Payment Gateways**: Supports Realex and Global Payments with PayPal fallback.
- **Card Validation**: MOD10 (Luhn algorithm), expiry checks, and AVS.
- **Encrypted Storage**: Securely stores card details.
- **PCI Compliance**: Built-in tools to meet PCI standards.
- **Recurring Payments**: Easy setup for subscription models.

---

## Installation

- Install the Package
```bash
pip install -e git+https://github.com/fmalina/django-pay.git#egg=pay
```
- Add `pay` to your `INSTALLED_APPS` in `settings.py`:
```python
INSTALLED_APPS = [
    ...,
    'pay',
]
```
- Include pay URLs in your project's `urls.py` file:
```python
from django.urls import include, path

urlpatterns = [
    ...,
    path('pay/', include('pay.urls')),
]
```
- Customize settings as needed (see `pay/app_settings.py` for options).
- Apply migrations
```bash
./manage.py migrate pay
```

## Usage
### Quick Start
Add a subscription link to your templates:
```html
<a href="{% url 'subscribe' %}">Subscribe</a>
```

### Recurring Charges
Set up a cron job using the provided `crontab.txt` for automated charges.
