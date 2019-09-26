from email.mime.image import MIMEImage
import os
from time import sleep

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import timezone

from guests.models import Party, MEALS

INVITATION_TEMPLATE = 'guests/email_templates/invitation.html'


def guess_party_by_invite_id_or_404(invite_id):
    try:
        return Party.objects.get(invitation_id=invite_id)
    except Party.DoesNotExist:
        if settings.DEBUG:
            # in debug mode allow access by ID
            return Party.objects.get(id=int(invite_id))
        else:
            raise Http404()


def get_invitation_context(party):
    return {
        'title': "Storm and Elise",
        'main_image': 'Elise-and-Storm-0086.jpg',
        'main_color': '#ecf7fe',
        'font_color': '#454040',
        'page_title': "{} - You're Invited!".format(settings.GROOM_AND_BRIDE),
        # 'preheader_text': "You are invited!", # I don't want this, looks weird in phone notifications
        'invitation_id': party.invitation_id,
        'party': party,
        'meals': MEALS,
        'site_url': settings.WEDDING_WEBSITE_URL,
        'couple': settings.GROOM_AND_BRIDE
    }


def send_invitation_email(party, test_only=False, recipients=None):
    if recipients is None:
        recipients = party.guest_emails
    if not recipients:
        print('===== WARNING: no valid email addresses found for {} ====='.format(party))
        return

    context = get_invitation_context(party)
    context['email_mode'] = True
    template_html = render_to_string(INVITATION_TEMPLATE, context=context)
    template_text = "You're invited to {}'s wedding. To view this invitation, visit {} in any browser.".format(
        settings.GROOM_AND_BRIDE,
        reverse('invitation', args=[context['invitation_id']])
    )
    subject = "You're Invited!"
    # https://www.vlent.nl/weblog/2014/01/15/sending-emails-with-embedded-images-in-django/
    msg = EmailMultiAlternatives(subject, template_text, settings.DEFAULT_WEDDING_FROM_EMAIL, recipients,
                                 cc=settings.WEDDING_CC_LIST,
                                 reply_to=[settings.DEFAULT_WEDDING_REPLY_EMAIL])
    msg.attach_alternative(template_html, "text/html")
    msg.mixed_subtype = 'related'
    for filename in (context['main_image'], ):
        attachment_path = os.path.join(os.path.dirname(__file__), 'static', 'invitation', 'images', filename)
        with open(attachment_path, "rb") as image_file:
            msg_img = MIMEImage(image_file.read())
            msg_img.add_header('Content-ID', '<{}>'.format(filename))
            msg_img.add_header('Content-Disposition', "attachment; filename= %s" % context['couple'])
            msg.attach(msg_img)

    print('sending invitation to {} ({})'.format(party.name, ', '.join(recipients)))
    if not test_only:
        try:
            msg.send()
        except:
            sleep(3)  # try again
            msg.send()


def send_all_invitations(test_only, mark_as_sent):
    to_send_to = Party.in_default_order().filter(is_invited=True, invitation_sent=None).exclude(is_attending=False)
    for party in to_send_to:
        send_invitation_email(party, test_only=test_only)
        if mark_as_sent:
            party.invitation_sent = timezone.now()
            party.save()
        print("All Done!")
