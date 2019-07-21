from django.conf import settings
from django.shortcuts import render
from guests.save_the_date import SAVE_THE_DATE_CONTEXT_MAP


def home(request):
    if settings.WIP_PAGE:
        return render(request, 'wip.html')
    else:
        return render(request, 'home.html', context={
            'save_the_dates': SAVE_THE_DATE_CONTEXT_MAP,
            'support_email': settings.DEFAULT_WEDDING_REPLY_EMAIL,
        })
