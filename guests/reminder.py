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

REMINDER_TEMPLATE = 'guests/email_templates/reminder.html'


def get_reminder_context(party):
    return {
        'title': "Storm and Elise",
        'main_image': 'Storm_and_Elise_0061.jpg',
        'main_color': '#ecf7fe',
        'font_color': '#454040',
        'page_title': "{} - We're getting married!".format(settings.GROOM_AND_BRIDE),
        'invitation_id': party.invitation_id,
        'party': party,
        'site_url': settings.WEDDING_WEBSITE_URL,
        'couple': settings.GROOM_AND_BRIDE
    }


def send_reminder_email(party, test_only=False, recipients=None):
    if recipients is None:
        recipients = party.guest_emails
    if not recipients:
        print('===== WARNING: no valid email addresses found for {} ====='.format(party))
        return

    context = get_reminder_context(party)
    context['email_mode'] = True
    template_html = render_to_string(REMINDER_TEMPLATE, context=context)
    template_text = "You're invited to {}'s wedding. To view this invitation, visit {} in any browser.".format(
        settings.GROOM_AND_BRIDE,
        reverse('invitation', args=[context['invitation_id']])
    )
    subject = "Reminder - December 28th, 2019"
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

    print('sending reminders to {} ({})'.format(party.name, ', '.join(recipients)))
    if not test_only:
        try:
            msg.send()
        except:
            sleep(3)  # try again
            print('Trying again...')
            msg.send()


def send_all_reminders(test_only, mark_as_sent):
    to_send_to = Party.in_default_order().filter(is_invited=True, is_attending=True, reminder_sent__isnull=True)
    for party in to_send_to:
        send_reminder_email(party, test_only=test_only)
        if mark_as_sent:
            party.reminder_sent = timezone.now()
            party.save()
    print("All Done!")
