from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from pay import app_settings
from pay.models import Payment
from pay.utils import get_amount

from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
import logging


PAYPAL_URL = 'https://www.paypal.com/cgi-bin/webscr'

User = get_user_model()


@login_required
def paypal(request):
    plan = request.user.subscription.plan

    url = ['%s?' % PAYPAL_URL]
    plan_days = int(plan)
    # also in listings_tags plus
    amount = get_amount(plan)

    p = Payment(user=request.user, amount=amount, method='pp')
    p.save()
    request.session['payment'] = p.id
    # breakdown per month
    # months = plan_days // 30
    # if months > 1:
    #    amount = Decimal(amount) / int(months)
    item = app_settings.PAY_FOR_NAME.format(
        plan=request.user.subscription.get_plan_display(),
        name=request.user.get_full_name()
    )
    params = {
        'cmd': '_xclick',
        'custom': p.id,
        'return': app_settings.PAY_SITE_URL + reverse('complete'),
        'cancel_return': app_settings.PAY_SITE_URL,
        'business': app_settings.PAY_PAYPAL_EMAIL,
        'currency_code': app_settings.PAY_CURRENCY,
        'amount': amount,
        'item_number': int(plan),
        'item_name': item
    }
    # if months > 1:
    #     params['quantity'] = int(months)
    for k, v in params.items():
        url.append('%s=%s' % (k, urllib.parse.quote(str(v))))
    url = '&'.join(url)
    return redirect(url)


def confirm_ipn_data(data):
    data['cmd'] = "_notify-validate"
    params = bytes(data.urlencode(), 'utf8')
    logging.info('PayPal data:', data)
    req = urllib.request.Request(PAYPAL_URL)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    fo = urllib.request.urlopen(req, params).read()
    if fo == "VERIFIED":
        logging.info("VERIFIED")
        return True
    logging.info("Payment verification failed:\n%s" % fo[:20])
    return False


@never_cache
@csrf_exempt
def ipn(request):
    logging.basicConfig(filename=app_settings.PAY_LOG, level=logging.INFO)
    sane = True
    now = datetime.now()
    if not request.method == "POST":
        logging.info("Just testing.")
        sane = False
    else:
        data = request.POST.copy()
        logging.info(data)
        if not confirm_ipn_data(data):
            pass
            # sane = False
    if sane:
        status = data.get('payment_status', 'unknown').strip()
        logging.info("Status: %s" % status)
        if status != "Completed":
            logging.info("Ignoring IPN data for non-complete payment.")
            sane = False
    if sane:
        days = int(data.get('item_number', '30').strip())
        p_pk = int(data.get('custom', '0').strip())
        if not p_pk:
            return HttpResponse('Paid using account email.')
        p = Payment.objects.get(pk=p_pk)
        u = User.objects.get(pk=p.user_id)
        app_settings.PAY_SUCCESS_CALLBACK(u, days)
        p.complete = True
        p.save()
        logging.info("\n%s purchased plan: %d.\n" % (
            u.username,
            days
        ))
    return HttpResponse('ok')
