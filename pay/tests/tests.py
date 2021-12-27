from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from pay.models import Subscription
from pay.realex import auth_payment
from pay.tests.test_models import create_test_card, create_test_user

User = get_user_model()


class SubTestCase(TestCase):
    """RealAuth test cards

    CVV2/CVC - Any 3-digit number can be used for testing purposes.
    Expiry Date - Any date in the future can be used.
    Card Types & Currencies - Your test account may not be set up for all
        currency and card type combinations. If you require a specific currency
        or card type set up for testing please contact support@realexpayments.com
        The currencies and card types available on your live account will be
        determined by your merchant services agreement with your bank.
    """
    def test_cards(self):
        tests = (
            (('GBP', '4000166842489115'), (False, '101', 'DECLINED')),  # VISA
            (('GBP', '5425232820001308'), (False, '101', 'DECLINED')),  # MC
            (('GBP', '374101012180018'), (False, '507', 'currency/card combination not allowed'))  # AMEX
        )

        def check(currency, cardnumber):
            user = create_test_user()
            card = create_test_card(user, cardnumber)
            amount = 30

            p, review_needed = auth_payment(card, amount, currency=currency)
            r = p.cardreceipt
            # 505: IP not whitelisted. 504: There is no such merchant id.
            if r.reason_code in ('505', '504'):
                print('Skipping integration test.')
                print('Realex:', r.details)
                return 'SKIP'
            return p.complete, r.reason_code, r.details

        for test in tests:
            test_func_args, expected_result = test
            result = check(*test_func_args)
            if result != 'SKIP':
                self.assertEquals(result, expected_result, test_func_args)
