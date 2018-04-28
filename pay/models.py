from django.db import models
from django.conf import settings
from datetime import datetime, date, timedelta
from Crypto.Cipher import Blowfish
from django.conf import settings
from pay import app_settings
import base64

MONTH_CHOICES = [('', 'Month')] + [(m, '%02d' % m) for m in range(1, 12+1)]
year = int(date.today().year)
YEAR_CHOICES = [('', 'Year')] + [(y, y) for y in range(year, year + 10)]
AVS_RESPONSES = (
    ('M', 'Matched'),
    ('N', 'Not Matched'),
    ('I', 'Problem with check'),
    ('U', 'Unable to check'),  # not certified etc
    ('P', 'Partial Match')
)
PAYMENT_METHODS = (
    ('cc', 'Credit/Debit card'),
    ('pp', 'PayPal'),
)
CURRENCIES = (
    ('GBP', '£'),
    ('EUR', '€'),
    ('USD', '$'),
)


class CardNumber(models.Model):
    """Card number (PAN)
    Delete, when not needed anymore.
    """
    paycard = models.OneToOneField('pay.PayCard', primary_key=True,
                                   on_delete=models.CASCADE)
    encrypted = models.CharField('Encrypted PAN', max_length=40,
        blank=True, editable=False)

    def ending(self):
        return self.decrypted[-4:]

    def obscured(self):
        xxxx = ''
        i = 0
        for x in self.decrypted:
            i = i + 1
            if i == 4:
                str = 'X '
                i = 0
            else:
                str = 'X'
            xxxx = xxxx + str
        return xxxx[0:-5] + ' ' + self.ending()

    def __str__(self):
        return self.obscured()

    @property
    def decrypted(self):
        return _decrypt_code(self.encrypted)


class PayCard(models.Model):
    """Card details that can be kept indefinitely with payments/transactions.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             null=True, blank=True, on_delete=models.SET_NULL)
    cardnumber_ending = models.CharField('Card number (last 4 digits)',
        max_length=4, blank=True)
    holder = models.CharField('Card holder’s name', max_length=75, blank=True)
    address = models.CharField('Billing address', max_length=150, blank=True)
    postcode = models.CharField('Billing postcode', max_length=15, blank=True)
    expire_month = models.IntegerField('Expiration month',
        choices=MONTH_CHOICES, null=True, blank=True)
    expire_year = models.IntegerField('Expiration year',
        choices=YEAR_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now, editable=False)

    def store_no(self, cardnumber_clear, cvv_clear):
        """Take as input a valid cc, encrypt it and store the last 4 digits
        in a visible form
        """
        encrypted = _encrypt_code(cardnumber_clear)
        cardnumber = CardNumber(paycard=self, encrypted=encrypted)
        cardnumber.save()

        if app_settings.PAY_STORE_CVV:
            encrypted = _encrypt_code(cvv_clear)
            cvv = CVV(paycard=self, encrypted=encrypted)
            cvv.save()

        self.cardnumber_ending = cardnumber.ending()

        if not self.pk or self.cardnumber_ending:
            self.save()

    def expdate(self):
        mm = str(self.expire_month).zfill(2)
        yy = str(self.expire_year)[-2:]
        return mm + yy

    def expired(self):
        y, m = datetime.now().strftime('%Y %m').split()
        # Subscription.objects.filter(expire_year__lte=y, expire_month__lte=m)
        if self.expire_year <= int(y) and self.expire_month <= int(m):
            return True
        return False

    def card_type(self):
        """Return card type based on the card number

        Regexes would look like:
        CC_PATTERNS = {
            'VISA': '^4([0-9]{12,15})$', # Visa
            'MC':   '^5[1-5][0-9]{14}$', # Mastercard
            'AMEX': '^3[47][0-9]{13}$', # American Express
        }
        """
        if not hasattr(self, 'cardnumber'):
            return 'deleted'

        n = str(self.cardnumber.decrypted)
        if not n:
            return ''
        l = len(n)
        n1, n2 = int(n[:1]), int(n[:2])
        t = 'INVALID'
        if l == 15:
            if n2 in (34, 37):
                t = 'AMEX'
        if l == 13:
            if n1 == 4:
                t = 'VISA'
        if l == 16:
            if 50 <= n2 <= 69:
                t = 'MC'
            if n1 == 4:
                t = 'VISA'
        return t

    def logo_img(self):
        return 'pay/img/logo_%s.svg' % self.card_type().lower()

    def __str__(self):
        return 'ending in %s' % self.cardnumber_ending


class CVV(models.Model):
    """Encrypted CVV for temporary storage. Delete, when not needed anymore.
    Optional Non-PCI compliant integration for room booking deposit protection.
    PAY_STORE_CVV setting must be set to True to enable.
    """
    paycard = models.OneToOneField('pay.PayCard', primary_key=True,
                                   on_delete=models.CASCADE)
    encrypted = models.CharField('Encrypted CVV', max_length=40,
        blank=True, editable=False)

    def __str__(self):
        return 'XXX'

    @property
    def decrypted(self):
        return _decrypt_code(self.encrypted)


def _decrypt_code(code):
    """Decrypt code encrypted by _encrypt_code
    """
    secret_key = app_settings.PAY_SECRET_KEY
    encryption_object = Blowfish.new(secret_key)
    # strip padding from decrypted credit card number
    return encryption_object.decrypt(base64.b64decode(code)).decode().rstrip('X')


def _encrypt_code(code):
    """Encrypt CC codes or code fragments
    """
    secret_key = app_settings.PAY_SECRET_KEY
    encryption_object = Blowfish.new(secret_key)
    # block cipher length must be a multiple of 8
    padding = ''
    if (len(code) % 8) != 0:
        padding = 'X' * (8 - (len(code) % 8))
    return base64.b64encode(encryption_object.encrypt(code + padding)).decode()


class Subscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True,
                                on_delete=models.CASCADE)
    plan = models.IntegerField('Plan', choices=app_settings.PAY_PLAN_CHOICES,
                               null=True, blank=True, default=0)
    expires = models.DateTimeField('active until', null=True, blank=True)
    recurring = models.BooleanField('Auto-renew', default=False)
    updated_at = models.DateTimeField(default=datetime.now, editable=False)

    @property
    def is_active(self):
        if self.expires and self.expires > datetime.now():
            return True
        return False

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super(Subscription, self).save(*args, **kwargs)


class Payment(models.Model):
    """Payments via credit or debit card and PayPal
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             blank=True, null=True, on_delete=models.SET_NULL)
    method = models.CharField('Payment Method', blank=True, max_length=2,
                              choices=PAYMENT_METHODS, default='cc')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='GBP')
    complete = models.BooleanField('Complete', default=False)
    time_stamp = models.DateTimeField(default=datetime.now, editable=False)

    prefetch = ['user', 'user__img', 'user__subscription', 'cardreceipt']
    ordering = ['-time_stamp']

    @models.permalink
    def get_absolute_url(self):
        return 'receipt', [self.pk]

    def voidable(self):
        """Payments are voidable if completed by card within the last 24 hours
        """
        return self.complete and\
            hasattr(self, 'cardreceipt') and\
            self.time_stamp > datetime.now() - timedelta(days=1)

    def __str__(self):
        return '%s - %s - %s %s' % (self.pk, self.user, self.amount, self.currency)


class CardReceipt(models.Model):
    """Result of a card transaction.
    """
    payment = models.OneToOneField('pay.Payment', primary_key=True, on_delete=models.CASCADE)
    paycard = models.ForeignKey('pay.PayCard', blank=True, null=True, on_delete=models.SET_NULL)
    details = models.CharField(blank=True, max_length=255)
    authcode = models.CharField(blank=True, max_length=20)
    reference = models.CharField(blank=True, max_length=20)
    reason_code = models.CharField(blank=True, max_length=20)

    avs_address = models.CharField('AVS address check', max_length=1,
        choices=AVS_RESPONSES, blank=True)
    avs_postcode = models.CharField('AVS postcode check', max_length=1,
        choices=AVS_RESPONSES, blank=True)

    def __str__(self):
        return self.details
