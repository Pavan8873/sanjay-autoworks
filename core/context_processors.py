from django.conf import settings

def app_settings(request):
    return {
        "SHOP_NAME": settings.SHOP_NAME,
        "SHOP_ADDRESS": settings.SHOP_ADDRESS,
        "SHOP_PHONE": settings.SHOP_PHONE,
        "SHOP_GSTIN": settings.SHOP_GSTIN,
        "SHOP_EMAIL": settings.SHOP_EMAIL,
        "GST_RATE": settings.GST_RATE,
    }
