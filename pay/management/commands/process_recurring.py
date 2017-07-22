from django.core.management.base import BaseCommand
from pay.models import Subscription
from pay.realex import auth_payment
from pay.views import get_amount
from datetime import datetime, timedelta
import time


def charge(s):
    last_payment = s.user.payment_set.filter(complete=True).last()
    if last_payment.method == 'pp':
        print('Paypal not supported')
    else:
        card = last_payment.cardreceipt.paycard
        cvv = getattr(card, 'cvv', None)
        if cvv:
            cvv = cvv.decrypted

        amount = get_amount(s.plan)
        print()
        print(s.user, s.plan, amount)
        p, review_needed = auth_payment(card, amount, cvv)
        if p.complete:
            s.expires = s.expires + timedelta(days=s.plan)
            s.save()
            print('Success, charged', p.amount)
        else:
            print('Failure', p.cardreceipt.details)


class Command(BaseCommand):
    """ Daily batch processing recurring charges.
    """
    def handle(self, *args, **kwargs):
        now = datetime.now()
        tomorrow = now + timedelta(hours=24)
        print('Processing recurring charges:', now)
        for s in Subscription.objects.filter(expires__range=(now, tomorrow), recurring=True):
            charge(s)
