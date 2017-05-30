from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.conf import settings
from pay.models import PayCard, Subscription, Payment
from pay.forms import PayCardForm, SubscribeForm
from pay.realex import auth_payment, void_payment
from pay import app_settings
from datetime import datetime, timedelta
from decimal import Decimal
import urllib.request
import urllib.parse
import urllib.error
import logging

User = get_user_model()

PAYPAL_URL = 'https://www.paypal.com/cgi-bin/webscr'

def get_amount(plan):
    return Decimal(app_settings.PAY_PLANS[int(plan)][0])


@login_required
def subscribe(request):
    user = request.user
    s, created = Subscription.objects.get_or_create(user=user)
    plan = s.plan
    form = SubscribeForm(request.POST or None, initial={'plan': plan})
    if form.is_valid():
        print(form.cleaned_data)
        plan = form.cleaned_data.get('plan', 0)
        s.plan = plan
        s.save()
        return redirect('payment')

    return render(request, 'pay/plans.html', {
        'title': app_settings.PAY_TITLE,
        'plan': plan,
        'form': form
    })


@login_required
def use_card(request):
    user = request.user
    last_card = PayCard.objects.filter(user=user).last()

    # throttling payments to avoid duplicates
    cutoff = datetime.now() - timedelta(minutes=app_settings.PAY_THROTTLE_TIME)
    if app_settings.PAY_THROTTLE_TIME and\
    request.POST and user.payment_set.filter(complete=True,
                                             time_stamp__gt=cutoff):
        msg = app_settings.PAY_MSG_THROTTLE
        return render(request, 'pay/duplicate.html', {'msg': msg})

    cc = PayCardForm(request.POST or None, label_suffix='',
                     initial={'last_card': bool(last_card)})
    if cc.is_valid():
        d = cc.cleaned_data
        if not d['last_card']:
            card = PayCard(
                expire_month=d['expire_month'],
                expire_year=d['expire_year'],
                holder=d['holder'],
                address=d['address'],
                postcode=d['postcode'],
                user=user
            )
            card.save()
            card.store_no(d['cardnumber'])
        else:
            card = last_card
        cvv = d['cvv']
        
        plan = user.subscription.plan
        amount = get_amount(plan)
        p, review_needed = auth_payment(card, amount, cvv=cvv)
        if p.complete:
            if not review_needed:
                app_settings.PAY_SUCCESS_CALLBACK(user, int(plan))
            else:
                app_settings.PAY_REVIEW_CALLBACK(user)
                messages.success(request, app_settings.PAY_MSG_SUCCESS)
            # email?
            request.session['payment'] = p.id
            return redirect(reverse('complete'))
        else:
            msg = app_settings.PAY_MSG_FAIL.format(error=p.cardreceipt.details)
            messages.warning(request, msg)

    return render(request, 'pay/payment.html', {
        'title': 'Pay by card',
        'last_card': last_card,
        'ssl': 'https://',
        'cc': cc
    })


@login_required
def paypal(request):
    plan = request.user.subscription.plan

    url = ['%s?' % PAYPAL_URL]
    plan_days = int(plan)
    # also in ad_tags premium
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


@login_required
def complete(request):
    try:
        pid = request.session['payment']
        p = get_object_or_404(Payment, pk=pid)
        del request.session['payment']
        return render(request, 'pay/completed.html', {'value': int(p.amount)})
    except KeyError:
        return redirect('/')


@login_required
def void(request, id):
    if not request.user.is_staff:
        raise
    p = get_object_or_404(Payment, pk=id)
    response = void_payment(p)
    p.complete = False
    p.save()
    messages.success(request, response.findtext('message'))
    return redirect('/details/%s' % p.user.pk)


@login_required
def receipt(request, id):
    p = get_object_or_404(Payment, pk=id)

    def format_vat(n):
        return "%0.2f" % round(n, 2)

    if request.user == p.user or request.user.is_staff:
        if p.complete:
            vat = p.amount / 120 * 20
            pre_vat = p.amount - vat
            return render(request, 'pay/receipt.html', {
                'payment': p,
                'pre_vat': format_vat(pre_vat),
                'vat': format_vat(vat),
                'email': settings.ADMIN_EMAIL,
                'title': 'Receipt %s' % p.pk
            })
        else:
            if request.user.is_staff:
                ls = p.user.payment_set.all()
                return render(request, 'dashboard/payment-failed.html', {
                    'ls': ls,
                    'count': ls.count(),
                    'payment': p,
                    'title': 'Attempts by %s' % p.user
                })
    raise Http404()


@login_required
def receipts(request):
    payments = request.user.payment_set.filter(complete=True)\
                           .only('id', 'user', 'amount', 'time_stamp')\
                           .order_by('-id')
    return render(request, 'pay/receipts.html', {
        'payments': payments
    })


@login_required
def paycards(request):
    paycards = PayCard.objects.filter(user=request.user)
    return render(request, 'pay/manage_cards.html', {
        'paycards': paycards
    })


@login_required
def add_card(request):
    form = PayCardForm(request.POST or None)
    if form.is_valid():
        d = form.cleaned_data
        cardnumber = d['cardnumber']

        d.pop('cardnumber', None)
        d.pop('last_card', None)
        d.pop('plan', None)
        d.pop('cvv', None)

        pc = PayCard(**d)
        pc.store_no(cardnumber)
        pc.user = request.user
        pc.save()
        return redirect('paycards')

    return render(request, 'pay/add_card.html', {
        'form': form
    })


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
