from django.conf.urls import url
from pay import views

urlpatterns = [
    url(r'^subscribe$', views.subscribe, name='subscribe'),
    url(r'^use_card$', views.use_card, name='payment'),
    url(r'^complete$', views.complete, name='complete'),
    url(r'^paycards$', views.paycards, name='paycards'),
    url(r'^add_card$', views.add_card, name='add_card'),
    url(r'^receipts$', views.receipts, name='receipts'),
    url(r'^receipt/(?P<id>[0-9]+)$', views.receipt, name='receipt'),
    url(r'^voiding/(?P<id>[0-9]+)$', views.void, name='void'),
    url(r'^paypal$', views.paypal, name='paypal'),
    url(r'^paypal_ipn$', views.ipn, name='paypal_ipn'),
]
