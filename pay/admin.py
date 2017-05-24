from pay.models import Payment, PayCard, CardReceipt, Subscription
from django.contrib import admin


class PayCardAdmin(admin.ModelAdmin):
    search_fields = ('cardnumber_ending', 'postcode')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'expires', 'recurring', 'updated_at')
    readonly_fields = ('updated_at',)


class CardReceiptInline(admin.StackedInline):
    model = CardReceipt
    readonly_fields = ('paycard', 'details', 'authcode', 'reference',
                    'reason_code', 'avs_address', 'avs_postcode')


class PaymentAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    search_fields = ('cardnumber_ending', 'postcode')
    list_display = ('time_stamp', 'user', 'amount', 'complete')
    readonly_fields = ('time_stamp',)
    inlines = [CardReceiptInline]


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(PayCard, PayCardAdmin)
admin.site.register(Payment, PaymentAdmin)
