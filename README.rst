Django app to work with subscriptions, payments and payment cards
=================================================================

.. image:: https://travis-ci.org/fmalina/django-pay.svg?branch=master
    :target: https://travis-ci.org/fmalina/django-pay

A reusable Django app to work with payments and credit cards.
Extracted from FlatmateRooms payment features
https://www.FlatmateRooms.co.uk/subscribe

- contains Realex payment gateway integration
- validation: card number (MOD10) and expiry, address verification system (AVS)
- models for encrypted storage of card numbers
- PayPal fallback offered as alternative payment method
- many PCI compliance requirements

Pay requires that you have a Realex account, which requires company
merchant account.

Installation (into a Django project)
------------------------------------

To get the latest version from GitHub

::

    pip3 install -e git+git://github.com/fmalina/django-pay.git#egg=pay

Add ``pay`` to your ``INSTALLED_APPS``

::

    INSTALLED_APPS = (
        ...,
        'pay',
    )

Configure your settings to suit, see pay/app_settings.py.

Add the ``pay`` URLs to your ``urls.py``

::

    urlpatterns = [
        ...
        url(r'^pay/', include('pay.urls')),
    ]

Create your tables

::

    ./manage.py migrate pay


Usage
-----
Simple integration works out of the box.

To pay from your interface, link:

::

    <a href="{% url 'subscribe' %}">Subscribe</a>


Recurring charges
-----------------
Add a cronjob as per crontab.txt


Contribute
----------
File issues. Fork and send pull requests. Tell developers integrating payments.


Dual Licensing
--------------

Commercial license
~~~~~~~~~~~~~~~~~~
If you want to use Django Pay to develop and run commercial projects and applications, the Commercial license is the appropriate license. With this option, your source code is kept proprietary.

Once purchased, you are granted a commercial BSD style license and all set to use Django Pay in your business.

`Small Team License (£400) <https://fmalina.github.io/pay.html?amount=400&msg=Django Pay Team license>`_
Small Team License for up to 8 developers

`Organization License (£1200) <https://fmalina.github.io/pay.html?amount=1200&msg=Django Pay Organisation License>`_
Commercial Organization License for Unlimited developers

Open source license
~~~~~~~~~~~~~~~~~~~
If you are creating an open source application under a license compatible with the GNU GPL license v3, you may use Django Pay under the terms of the GPLv3.
