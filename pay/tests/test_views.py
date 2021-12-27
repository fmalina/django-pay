from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, redirect, render

from pay.tests.test_models import create_test_user


def index(request):
    # create dummy account and login the current user
    user = create_test_user()
    user = authenticate(username=user.username, password='testpw')
    login(request, user)

    return render(request, 'index.html', {
        'user': user
    })
