from email.mime.image import MIMEImage
import os
from time import sleep

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone

from guests.models import Party

THANK_YOU_TEMPLATE = 'guests/email_templates/thank_you.html'


def get_thank_you_context(party):
    return {
        'title': "Storm and Elise",
        'main_image': 'Formals-337-EE-crop-min.jpg',
        'main_color': '#ecf7fe',
        'font_color': '#454040',
        'page_title': "{} - Thank you for coming!".format(settings.GROOM_AND_BRIDE),
        'invitation_id': party.invitation_id,
        'party': party,
        'site_url': settings.WEDDING_WEBSITE_URL,
        'couple': settings.GROOM_AND_BRIDE
    }


def send_thank_you_email(party, test_only=False, recipients=None):
    if recipients is None:
        recipients = party.guest_emails
    if not recipients:
        print('===== WARNING: no valid email addresses found for {} ====='.format(party))
        return

    context = get_thank_you_context(party)
    context['email_mode'] = True
    template_html = render_to_string(THANK_YOU_TEMPLATE, context=context)
    template_text = "{} want to say thank you!.".format(
        settings.GROOM_AND_BRIDE,
        reverse('invitation', args=[context['invitation_id']])
    )
    subject = "Thank you for coming to our Wedding!"
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

    print('sending thank you\'s to {} ({})'.format(party.name, ', '.join(recipients)))
    if not test_only:
        try:
            msg.send()
        except:
            sleep(3)  # try again
            print('Trying again...')
            msg.send()


def send_all_thank_you(test_only, mark_as_sent):
    not_attending = Q(is_attending=False)
    no_gift_received = Q(received_gifts__isnull=True) | Q(received_gifts='')
    to_send_to = Party.in_default_order().filter(is_invited=True, receives_a_thank_you_note=True,
                                                 thank_you_sent__isnull=True).exclude(not_attending & no_gift_received)
    # TODO double check this query when data sanitation is complete
    for party in to_send_to:
        send_thank_you_email(party, test_only=test_only)
        if mark_as_sent:
            party.thank_you_sent = timezone.now()
            party.save()
    print("All Done!")
