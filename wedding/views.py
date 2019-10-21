from django.conf import settings
from django.shortcuts import render
from guests.save_the_date import SAVE_THE_DATE_CONTEXT_MAP


def home(request):
    if settings.WIP_PAGE:
        return wip(request)
    else:
        return sneak_peek(request)


def sneak_peek(request):
    return render(request, 'home.html', context={
            'save_the_dates': SAVE_THE_DATE_CONTEXT_MAP,
            'support_email': settings.DEFAULT_WEDDING_REPLY_EMAIL,
            'groom_and_bride': settings.GROOM_AND_BRIDE,
        })


def wip(request):
    return render(request, 'wip.html', context={'groom_and_bride': settings.GROOM_AND_BRIDE})


def beaches(request):
    return render(request, 'beaches.html')