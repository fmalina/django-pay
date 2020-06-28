from django.db import models
from django.auth.models import get_auth_user_model
from django.messages import messages
import random
import decimal
import datetime



User = get_auth_user_model()


class BankAccount(models.Model):
    user = models.ForeignKey(User)
    sort_code = models.CharField(max_length=6)
    account_no = models.CharField(max_length=12)
    verified = models.BooleanField(default=False)
    verification_amount = models.DecimalField(max_digits=3, decimal_places=2)
    verification_attempts = models.IntegerField(default=0)

    MAX_VERIFICATION_ATTEMPTS = 3

    def attemps_left(self):
        return MAX_VERIFICATION_ATTEMPTS - self.verification_attempts

    def get_verification_amount(self):
        return decimal.Decimal(random.random())

    def pay_to_this_account(self, amount):
        """ Handle BACS payment
        """
        pass

    def init_verify_account(self):
        self.verification_amount = self.get_verification_amount()
        self.pay_to_this_account(self.verification_amount)
        self.save()

    def finish_verify_account(self, amount):
        if not self.attemps_left():
            return "Verification failed. Contact customer services."

        if amount == self.verification_amount:
            self.verified = True
            self.save()
            messages.success('Account successfully verified.')
        else:
            self.verification_attempts += 1
            self.save()
            messages.error("Amount doesn't match. %s attemps left" % self.attemps_left())


class RentPayment(models.Model):
    paid_by = models.ForeignKey(User, verbose_name="tenant/guest/flatmate/lodger")
    paid_to = models.ForeignKey(BankAccount, verbose_name="landlord/host/agent")
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    time_stamp = models.DateTimeField(default=datetime.datetime.now)


