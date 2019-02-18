from django.urls import path
from pay import views
from pay import paypal

urlpatterns = [
    path('subscribe', views.subscribe, name='subscribe'),
    path('payment', views.payment, name='payment'),
    path('complete', views.complete, name='complete'),
    path('paycards', views.paycards, name='paycards'),
    path('add_card', views.add_card, name='add_card'),
    path('receipts', views.receipts, name='receipts'),
    path('receipts/<int:user_id>', views.receipts,
        name='user_receipts'),
    path('subscription', views.subscription, name='subscription'),
    path('subscription/<int:user_id>', views.subscription,
        name='user_subscription'),
    path('receipt/<int:pk>', views.receipt, name='receipt'),
    path('voiding/<int:pk>', views.void, name='void'),
    path('paypal', paypal.paypal, name='paypal'),
    path('paypal_ipn', paypal.ipn, name='paypal_ipn'),
]
