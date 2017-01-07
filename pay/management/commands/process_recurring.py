from django.core.management.base import BaseCommand
from pay.models import Subscription
from pay.realex import auth_payment
from pay.views import get_amount
from datetime import datetime, timedelta
import time


def charge(s):
    last_payment = s.user.payment_set.filter(complete=True, method='cc').last()
    card = last_payment.card
    amount = get_amount(s.plan)
    p, review_needed = auth_payment(card, amount)
    if p.complete:
        s.expires = s.expires + timedelta(days=s.plan)
        s.save()


class Command(BaseCommand):
    """ Daily batch recurring charge processing.
    """
    def handle(self, *args, **kwargs):
        now = datetime.now()
        yesterday = now - timedelta(hours=24)

        for s in Subscription.objects.filter(expires__range=(yesterday, now)):
            charge(s)
