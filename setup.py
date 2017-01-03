# -*- encoding: utf-8 -*-
from setuptools import setup, find_packages
import pay as app

setup(
    name="pay",
    version=app.__version__,
    description='Django payment credit and debit card Realex/Paypal subscriptions',
    long_description=open('README.rst').read(),
    license='BSD License',
    platforms=['OS Independent'],
    keywords='realex, paypal, credit card, django, app, subscriptions',
    author='fmalina',
    author_email='fmalina@gmail.com',
    url="https://github.com/fmalina/django-pay",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open('requirements.txt').read().split(),
)
