import base64
from collections import namedtuple
import random
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import ListView
from guests import csv_import
from guests.follow_up import send_follow_up_email, FOLLOW_UP_TEMPLATE, get_follow_up_context
from guests.invitation import get_invitation_context, INVITATION_TEMPLATE, guess_party_by_invite_id_or_404, \
    send_invitation_email
from guests.models import Guest, MEALS, Party
from guests.reminder import get_reminder_context, REMINDER_TEMPLATE, send_reminder_email
from guests.save_the_date import get_save_the_date_context, send_save_the_date_email, SAVE_THE_DATE_TEMPLATE, \
    SAVE_THE_DATE_CONTEXT_MAP
from guests.thank_you import send_thank_you_email, get_thank_you_context, THANK_YOU_TEMPLATE


class GuestListView(ListView):
    model = Guest


@login_required
def export_guests(request):
    export = csv_import.export_guests()
    response = HttpResponse(export.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=all-guests.csv'
    return response


@login_required
def dashboard(request):
    parties_with_pending_invites = Party.objects.filter(
        is_invited=True, is_attending=None, invitation_sent__isnull=False
    ).order_by('category', 'name')
    parties_with_unopen_invites = parties_with_pending_invites.filter(invitation_opened=None)
    parties_with_open_unresponded_invites = parties_with_pending_invites.exclude(invitation_opened=None)
    attending_guests = Guest.objects.filter(is_attending=True)
    responded_parties = Party.objects.filter(responded_to_invitation__isnull=False)
    # guests_without_meals = attending_guests.filter(
    #     is_child=False
    # ).filter(
    #     Q(meal__isnull=True) | Q(meal='')
    # ).order_by(
    #     'party__category', 'first_name'
    # )
    # meal_breakdown = attending_guests.exclude(meal=None).values('meal').annotate(count=Count('*'))
    category_breakdown = attending_guests.values('party__category').annotate(count=Count('*'))
    sent_save_the_dates = Guest.objects.filter(party__save_the_date_sent__isnull=False)
    return render(request, 'guests/dashboard.html', context={
        'guests': Guest.objects.filter(is_attending=True).count(),
        'possible_guests': Guest.objects.filter(party__is_invited=True).exclude(is_attending=False).count(),
        'not_coming_guests': Guest.objects.filter(is_attending=False).order_by('party__name', 'first_name'),
        'pending_invites': parties_with_pending_invites.count(),
        'pending_guests': Guest.objects.filter(party__is_invited=True, is_attending=None).count(),
        # 'guests_without_meals': guests_without_meals,
        'parties_with_unopen_invites': parties_with_unopen_invites,
        'parties_with_open_unresponded_invites': parties_with_open_unresponded_invites,
        'unopened_invite_count': parties_with_unopen_invites.count(),
        'opened_save_the_date_count': sent_save_the_dates.filter(party__save_the_date_opened__isnull=False).count(),
        'unopened_save_the_date': Party.objects.filter(save_the_date_sent__isnull=False,
                                                       save_the_date_opened__isnull=True).order_by('category', 'name'),
        'total_save_the_dates': sent_save_the_dates.count(),
        'total_invites': Party.objects.filter(is_invited=True).count(),
        # 'meal_breakdown': meal_breakdown,
        'category_breakdown': category_breakdown,
        'responded_parties': responded_parties.order_by('category', '-responded_to_invitation'),
    })


def invitation(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    if party.invitation_opened is None:
        # update if this is the first time the invitation was opened
        party.invitation_opened = timezone.now()
        if party.follow_up_opened is None:
            # To track the follow up being opened too
            party.follow_up_opened = timezone.now()
        party.save()
    if request.method == 'POST':
        for response in _parse_invite_params(request.POST):
            guest = Guest.objects.get(pk=response.guest_pk)
            assert guest.party == party
            guest.is_attending = response.is_attending
            guest.meal = response.meal
            guest.save()
        if request.POST.get('comments'):
            comments = request.POST.get('comments')
            party.comments = comments if not party.comments else '{}; {}'.format(party.comments, comments)
        party.is_attending = party.any_guests_attending
        party.responded_to_invitation = timezone.now()
        party.save()
        return HttpResponseRedirect(reverse('rsvp-confirm', args=[invite_id]))
    return render(request, template_name='guests/invitation.html', context={
        'party': party,
        'meals': MEALS,
    })


InviteResponse = namedtuple('InviteResponse', ['guest_pk', 'is_attending', 'meal'])


def _parse_invite_params(params):
    responses = {}
    for param, value in params.items():
        if param.startswith('attending'):
            pk = int(param.split('-')[-1])
            response = responses.get(pk, {})
            response['attending'] = True if value == 'yes' else False
            responses[pk] = response
        elif param.startswith('meal'):
            pk = int(param.split('-')[-1])
            response = responses.get(pk, {})
            response['meal'] = value
            responses[pk] = response

    for pk, response in responses.items():
        yield InviteResponse(pk, response['attending'], response.get('meal', None))


def rsvp_confirm(request, invite_id=None):
    party = guess_party_by_invite_id_or_404(invite_id)
    return render(request, template_name='guests/rsvp_confirmation.html', context={
        'party': party,
        'support_email': settings.DEFAULT_WEDDING_REPLY_EMAIL,
    })


@login_required
def invitation_email_preview(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    context = get_invitation_context(party)
    return render(request, INVITATION_TEMPLATE, context=context)


@login_required
def invitation_email_test(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    send_invitation_email(party, recipients=[settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


@login_required
def follow_up_email_preview(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    context = get_follow_up_context(party)
    return render(request, FOLLOW_UP_TEMPLATE, context=context)


@login_required
def follow_up_email_test(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    send_follow_up_email(party, recipients=[settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


@login_required
def reminder_email_preview(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    context = get_reminder_context(party)
    return render(request, REMINDER_TEMPLATE, context=context)


@login_required
def reminder_email_test(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    send_reminder_email(party, recipients=[settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


def thank_you_email_preview(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    context = get_thank_you_context(party)
    return render(request, THANK_YOU_TEMPLATE, context=context)


@login_required
def thank_you_email_test(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    send_thank_you_email(party, recipients=[settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


def save_the_date_random(request):
    template_id = random.choice(SAVE_THE_DATE_CONTEXT_MAP.keys())
    return save_the_date_preview(request, template_id)


def save_the_date_preview(request, template_id):
    context = get_save_the_date_context(template_id)
    context['email_mode'] = False
    return render(request, SAVE_THE_DATE_TEMPLATE, context=context)


def save_the_date_redirect(request, save_the_date_id):
    """Save if save the date has been opened (from the email) or not."""
    try:
        party = Party.objects.get(save_the_date_id=save_the_date_id)
    except Party.DoesNotExist:
        if settings.DEBUG:
            # in debug mode allow access by ID
            party = Party.objects.get(id=int(save_the_date_id))
        else:
            # Oh well we tried lol, bring em back home
            return HttpResponseRedirect(reverse('home'))

    if not party.save_the_date_opened:
        # Only save the first time
        party.save_the_date_opened = timezone.now()
        party.save()
    return HttpResponseRedirect(reverse('home'))


@login_required
def test_email(request, template_id):
    context = get_save_the_date_context(template_id)
    send_save_the_date_email(context, [settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


def _base64_encode(filepath):
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read())
