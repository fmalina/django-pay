from pay.models import Payment, PayCard, Subscription
from django.contrib import admin


class PayCardAdmin(admin.ModelAdmin):
    search_fields = ('cardnumber_ending', 'postcode')


class PaymentAdmin(admin.ModelAdmin):
    search_fields = ('cardnumber_ending', 'postcode')


admin.site.register(PayCard, PayCardAdmin)
admin.site.register(Payment, PaymentAdmin)
