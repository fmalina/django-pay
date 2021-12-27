import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from hashlib import sha1
from time import strftime

from django.conf import settings
from django.template.loader import render_to_string
from lxml import etree

from pay import app_settings
from pay.models import CardReceipt, PayCard, Payment

POST_URL = 'https://epage.payandshop.com/epage-remote.cgi'
DT_FORMAT = '%Y%m%d%H%M%S'


def call_realex(request_type, payment, context_dict):
    """Create and post XML request to Realex payment gateway.
    Add time_stamp to <orderid> countering double payment issues when testing.
    Payment time_stamp is final allowing voids, but differs everytime allowing tests.
    """
    p, d = payment, context_dict
    d['test'] = False  # settings.DEBUG
    d['orderid'] = str(p.pk) + '_' + p.time_stamp.strftime(DT_FORMAT)
    d['time_stamp'] = strftime(DT_FORMAT)  # current time
    d['merchant_id'] = app_settings.PAY_REALEX_MERCHANT_ID
    d['request_type'] = request_type
    d['p'] = p
    if request_type == 'auth':
        d['amount'] = str(int(p.amount * 100))  # in pences or cents
        d['currency'] = p.currency
    checkls = 'time_stamp merchant_id orderid amount currency cardnumber'.split()
    check = '.'.join([d[key] for key in checkls])

    def sha1_hash(s):
        return sha1(str(s).encode()).hexdigest()

    d['sha1hash'] = sha1_hash(sha1_hash(check) + '.' +\
                              app_settings.PAY_REALEX_PASSWORD)

    xml = render_to_string('pay/realex_request.xml', d)
    conn = urllib.request.Request(url=POST_URL, data=bytes(xml, 'utf8'))
    r = urllib.request.urlopen(conn).read()

    if settings.DEBUG:
        print('CALL:', xml)
        print('CHECK:', check)
        print('ANSWER:', r.decode(), end='\n\n\n')

    return etree.fromstring(r)


def void_payment(p):
    return call_realex('void', p, {'amount': '', 'currency': '', 'cardnumber': ''})


def auth_payment(card, amount, cvv=None, currency=app_settings.PAY_CURRENCY):
    now = datetime.now()
    p = Payment(
        user=card.user,
        method='C',
        amount=amount,
        currency=currency,
        complete=False,
        time_stamp=now - timedelta(microseconds=now.microsecond)
    )
    p.save()

    if not cvv:
        cvv = '000'
        if card.card_type() == 'AMEX':
            cvv = '0000'

    def numbers_only(addr):
        return ''.join([x for x in addr if x.isdigit()])

    adr = numbers_only(card.address)
    pst = numbers_only(card.postcode)
    avs = f"{pst}|{adr}"
    if avs == '|' or pst == '':
        avs = False

    r = call_realex('auth', p, {
        'cardnumber': card.cardnumber.decrypted,
        'card': card,
        'cvv': cvv,
        'avs': avs
    })

    receipt = CardReceipt(
        paycard=card,
        details=r.findtext('message'),
        authcode=r.findtext('authcode') or '',
        reference=r.findtext('pasref') or '',
        reason_code=r.findtext('result'),
        avs_address=r.findtext('avsaddressresponse') or '',
        avs_postcode=r.findtext('avspostcoderesponse') or ''
    )

    if p.pk != int(r.findtext('orderid').split('_')[0]):
        raise
    if receipt.reason_code == '00':
        p.complete = True
    p.save()

    receipt.payment = p
    receipt.save()

    try:  # TODO: save this in the DB
        card_country = r.find('cardissuer').find('countrycode').text
    except AttributeError:
        card_country = ''

    if card_country in app_settings.PAY_REALEX_HIGH_RISK_COUNTRIES:
        review_needed = 1
    else:
        review_needed = 0

    return p, review_needed


def bulk_delete_old_cardnumbers():
    old = datetime.now().year - 2
    for card in PayCard.objects.filter(expire_year__lt=old):
        print(card.expire_month, card.expire_year)
        card.cardnumber.delete()
