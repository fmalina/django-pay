from django.contrib import admin

from pay.models import CardReceipt, PayCard, Payment, Subscription


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
    search_fields = ('cardnumber_ending', 'postcode')
    list_display = ('time_stamp', 'user', 'amount', 'complete')
    readonly_fields = ('time_stamp',)
    inlines = [CardReceiptInline]


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(PayCard, PayCardAdmin)
admin.site.register(Payment, PaymentAdmin)
