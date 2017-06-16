from django.conf import settings
from django.core.mail import mail_managers
from datetime import datetime, timedelta


def add_expiry(user, days):
    start = datetime.now()
    if user.subscription.is_active:
        start = user.subscription.expires
    user.subscription.expires = start + timedelta(days=days)
    user.subscription.save()

def alert_review(user):
    mail_managers('Payment review required',
                  'Review payment from: %s' % user.username)


PAY_SUCCESS_CALLBACK = getattr(settings, 'PAY_SUCCESS_CALLBACK', add_expiry)
PAY_REVIEW_CALLBACK = getattr(settings, 'PAY_REVIEW_CALLBACK', alert_review)

PAY_MSG_SUCCESS = getattr(settings, 'PAY_MSG_SUCCESS', 'Success.')
PAY_MSG_FAIL = getattr(settings, 'PAY_MSG_FAIL',
    """{error}. We’ve had some issues processing your card.
    Please check card expiry and other details and try again.
    Alternatively, use PayPal instead.
    """)
PAY_MSG_THROTTLE = getattr(settings, 'PAY_MSG_THROTTLE',
    """You have successfully paid within the last 10 minutes. Please wait.
    A delay is in place to avoid accidently charging your card twice.
    It may take up to 10 minutes for your subscription to be processed.
    """)
PAY_TITLE = getattr(settings, 'PAY_TITLE', 'Choose your plan')
PAY_FOR_NAME = getattr(settings, 'PAY_FOR_NAME',
    '{plan} for {name} (activated immediately)')
PAY_SITE_URL = getattr(settings, 'PAY_SITE_URL', '')
PAY_CURRENCY = getattr(settings, 'PAY_CURRENCY', 'GBP')  #  EUR, USD
PAY_THROTTLE_TIME = getattr(settings, 'PAY_THROTTLE_TIME', 0)  # 0 minutes
PAY_SECRET_KEY = getattr(settings, 'PAY_SECRET_KEY', settings.SECRET_KEY)

PAY_REALEX_MERCHANT_ID = getattr(settings,
    'PAY_REALEX_MERCHANT_ID',
    'businessnamehere')
PAY_REALEX_PASSWORD = getattr(settings,
    'PAY_REALEX_PASSWORD',
    '*********')
PAY_REALEX_HIGH_RISK_COUNTRIES = getattr(settings,
    'PAY_REALEX_HIGH_RISK_COUNTRIES',
    ['US'])
PAY_REALEX_AMEX_ENABLED = getattr(settings,
    'PAY_REALEX_AMEX_ENABLED',
    False)
PAY_PAYPAL_EMAIL = getattr(settings,
    'PAY_PAYPAL_EMAIL',
    'fmalina@gmail.com')
PAY_RECEIPT_EMAIL = getattr(settings,
    'PAY_RECEIPT_EMAIL',
    settings.DEFAULT_FROM_EMAIL)

PAY_PLANS = getattr(settings,
    'PAY_PLANS', {
        30: ('29.00', '30 days - £29'),
        365: ('199.00', 'One year - £199'),
    })
PAY_PLAN_CHOICES = getattr(settings,
    'PAY_PLAN_CHOICES',
    [(days, amount_desc[1]) for days, amount_desc in PAY_PLANS.items()]
    )
PAY_LOG = getattr(settings, 'PAY_LOG', 'log')
