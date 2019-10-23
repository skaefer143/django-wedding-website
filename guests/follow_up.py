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

FOLLOW_UP_TEMPLATE = 'guests/email_templates/follow_up.html'


def get_follow_up_context(party):
    return {
        'title': "Storm and Elise",
        'main_image': 'Elise-and-Storm-0086.jpg',
        'main_color': '#ecf7fe',
        'font_color': '#454040',
        'page_title': "{} - You're Invited!".format(settings.GROOM_AND_BRIDE),
        'invitation_id': party.invitation_id,
        'party': party,
        'site_url': settings.WEDDING_WEBSITE_URL,
        'couple': settings.GROOM_AND_BRIDE
    }


def send_follow_up_email(party, test_only=False, recipients=None):
    if recipients is None:
        recipients = party.guest_emails
    if not recipients:
        print('===== WARNING: no valid email addresses found for {} ====='.format(party))
        return

    context = get_follow_up_context(party)
    context['email_mode'] = True
    template_html = render_to_string(FOLLOW_UP_TEMPLATE, context=context)
    template_text = "You're invited to {}'s wedding. To view this invitation, visit {} in any browser.".format(
        settings.GROOM_AND_BRIDE,
        reverse('invitation', args=[context['invitation_id']])
    )
    subject = "Have you RSVP'd yet?"
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

    print('sending follow ups to {} ({})'.format(party.name, ', '.join(recipients)))
    if not test_only:
        try:
            msg.send()
        except:
            sleep(3)  # try again
            print('Trying again...')
            msg.send()


def send_all_follow_ups(test_only, mark_as_sent):
    to_send_to = Party.in_default_order().filter(is_invited=True, is_attending=None, invitation_sent__isnull=False, follow_up_sent__isnull=True)\
        .exclude(responded_to_invitation__isnull=False)
    for party in to_send_to:
        send_follow_up_email(party, test_only=test_only)
        if mark_as_sent:
            party.follow_up_sent = timezone.now()
            party.save()
    print("All Done!")
