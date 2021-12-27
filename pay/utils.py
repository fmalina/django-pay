from decimal import Decimal

from pay import app_settings


def get_amount(plan):
    return Decimal(app_settings.PAY_PLANS[int(plan)][0])
