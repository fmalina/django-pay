from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from pay import app_settings
from pay.forms import PayCardForm, SubscribeForm, SubscriptionForm
from pay.models import PayCard, Payment, Subscription
from pay.realex import auth_payment, void_payment
from pay.utils import get_amount

User = get_user_model()


def get_user(request, user_id):
    user = request.user
    if user_id:
        user = get_object_or_404(User, id=user_id)
        if not user==request.user and not request.user.is_staff:
            return False
    return user


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
        'plans': app_settings.PAY_PLAN_CHOICES,
        'plan': plan,
        'form': form
    })


@login_required
def subscription(request, user_id=None):
    user = get_user(request, user_id)
    if not user:
        return HttpResponse('')
    s, created = Subscription.objects.get_or_create(user=user)
    form = SubscriptionForm(request.POST or None, instance=s)
    print(form.is_valid())
    if form.is_valid():
        form.save()
        messages.success(request, 'Subscription successfully updated.')
    return render(request, 'pay/subscription.html', {
        'form': form,
        'subscription': s
    })


@login_required
def payment(request):
    if not app_settings.PAY_REALEX_ENABLED:
        return redirect('paypal')
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
            card.store_no(d['cardnumber'], d['cvv'])
        else:
            card = last_card
        cvv = d['cvv']

        if d['recurring']:
            user.subscription.recurring = True
            user.subscription.save()

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
    plan = app_settings.PAY_PLANS[user.subscription.plan]
    plan_price, plan_name = plan[0], plan[1]

    return render(request, 'pay/payment.html', {
        'title': 'Pay by card',
        'last_card': last_card,
        'plan_name': plan_name,
        'plan_price': plan_price,
        'ssl': 'https://',
        'cc': cc,
        'amex_enabled': app_settings.PAY_REALEX_AMEX_ENABLED,
        'require_autorenew_consent': app_settings.PAY_REQUIRE_AUTORENEW_CONSENT
    })


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
    return redirect(f'/details/{p.user.pk}')


@login_required
def receipt(request, pk):
    p = get_object_or_404(Payment, pk=pk)

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
                'email': app_settings.PAY_RECEIPT_EMAIL,
                'title': f'Receipt {p.pk}'
            })
        else:
            if request.user.is_staff:
                ls = p.user.payment_set.all()
                return render(request, 'dashboard/payment-failed.html', {
                    'ls': ls,
                    'count': ls.count(),
                    'payment': p,
                    'title': f'Attempts by {p.user}'
                })
    raise Http404()


@login_required
def receipts(request, user_id=None):
    user = get_user(request, user_id)
    if not user:
        return HttpResponse('')
    payments = user.payment_set.filter(complete=True)\
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
        cvv = d['cvv']

        d.pop('cardnumber', None)
        d.pop('last_card', None)
        d.pop('plan', None)
        d.pop('cvv', None)

        pc = PayCard(**d)
        pc.user = request.user
        pc.save()
        pc.store_no(cardnumber, cvv)
        return redirect('paycards')

    return render(request, 'pay/add_card.html', {
        'form': form
    })
