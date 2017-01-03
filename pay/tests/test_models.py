from django.test import TestCase
from django.contrib.auth.models import User
from pay.models import Payment, PayCard
from decimal import Decimal

TEST_CARDS = {
 # www.paypalobjects.com/en_US/vhelp/paypalmanager_help/credit_card_numbers.htm
    'VISA': '4111 1111 1111 1111',
    'MC': '5555 5555 5555 4444',
    'AMEX': '3782 822 4631 0005',
}


def create_test_user():
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(
            first_name='Joe',
            last_name='Bloggs',
            username='joe.bloggs',
            email='fmalina@gmail.com',
            is_staff=True,
            is_superuser=True,
            password='testpw'
        )
        user.save()
    return user


def create_test_card(user, cardnumber):
    card = PayCard(
        user=user,
        holder='MR J BLOGGS',
        expire_month=1,
        expire_year=2020
    )
    card.store_no(cardnumber)
    card.save()
    return card


class PaymentTestCase(TestCase):
    def setUp(self):
        user = create_test_user()
        p = Payment(user=user, method='pp', amount=19.99)
        p.save()

        for card_type, cardnumber in TEST_CARDS.items():
            create_test_card(user, cardnumber)

    def test_model(self):
        p = Payment.objects.first()
        self.assertEqual(p.pk, 1)
        self.assertEqual(p.voidable(), False)
        self.assertEqual(p.amount, Decimal('19.99'))
        self.assertEqual(p.user.paycard_set.all().count(), 3)
