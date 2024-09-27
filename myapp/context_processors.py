# your_app/context_processors.py
from django.conf import settings

def stripe_keys(request):
    return {
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
    }