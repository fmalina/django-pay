from django import forms
from pay import models as pay_models
from pay import app_settings
import re


class CCNumberField(forms.CharField):
    ERR_CHARS = 'Card number can only contain numbers and spaces'
    ERR_LENGTH = 'Card number must be 14 to 19 numbers long'
    ERR_MOD10 = 'Card number entered is not valid credit or debit card number'

    def validate_mod10(self, n):
        """Check to make sure that the card passes a luhn mod-10 checksum
        """
        sum = 0
        num_digits = len(n)
        oddeven = num_digits & 1
        for i in range(0, num_digits):
            digit = int(n[i])
            if not ((i & 1) ^ oddeven):
                digit = digit * 2
            if digit > 9:
                digit = digit - 9
            sum = sum + digit
        return ((sum % 10) == 0)

    def strip_to_numbers(self, n):
        """Remove spaces from the number
        """
        if self.validate_chars(n):
            result = ''
            rx = re.compile('^[0-9]$')
            for d in n:
                if rx.match(d):
                    result += d
            return result
        else:
            raise Exception('Number has invalid digits')

    def validate_chars(self, n):
        """Check to make sure string only contains valid characters
        """
        return re.compile('^[0-9 ]*$').match(n) is not None

    def clean(self, value):
        value = forms.CharField.clean(self, value)
        if not self.validate_chars(value):
            raise forms.ValidationError(self.ERR_CHARS)
        value = self.strip_to_numbers(value)
        if value:
            if len(value) < 12 or len(value) > 19:
                raise forms.ValidationError(self.ERR_LENGTH)
        if not self.validate_mod10(value):
            raise forms.ValidationError(self.ERR_MOD10)
        return value


class SubscribeForm(forms.Form):
     plan = forms.ChoiceField(choices=app_settings.PAY_PLAN_CHOICES, initial=30,
                              required=False)


class SubscriptionForm(forms.ModelForm):
    class Meta:
        exclude = ['user', 'expires']
        model = pay_models.Subscription


class PayCardForm(forms.Form):
    cardnumber = CCNumberField(max_length=19, label='Card number', required=False)
    holder = forms.CharField(max_length=75, label='Cardholder’s name', required=False)
    address = forms.CharField(max_length=150, label='Billing address *',
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 25}), required=False)
    postcode = forms.CharField(max_length=15, label='Billing postcode *', required=False)
    expire_month = forms.ChoiceField(choices=pay_models.MONTH_CHOICES, label='Expires on', required=False)
    expire_year = forms.ChoiceField(choices=pay_models.YEAR_CHOICES, required=False)
    last_card = forms.BooleanField(initial=False, widget=forms.HiddenInput)
    cvv = forms.CharField(max_length=4, label='Security code (CVV)', required=False)

    def clean_holder(self):
        holder = self.cleaned_data['holder']
        import unicodedata
        return unicodedata.normalize('NFKD', str(holder)).encode('ASCII', 'ignore')

    def clean(self):
        data = self.cleaned_data
        method = data.get('method')
        last_card = data.get('last_card')

        def check(field, error):
            if not data.get(field):
                self._errors[field] = self.error_class([error])
                data.pop(field, None)

        # Conditional validation:
        if not last_card:
            check('cardnumber', 'Please enter your card number.')
            check('expire_month', 'Select your card expiration month.')
            check('expire_year', 'Select expiration year.')
            check('holder', 'Enter name of the cardholder.')
        check('cvv', 'Enter the security code.')
        return data
