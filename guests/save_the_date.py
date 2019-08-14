from __future__ import unicode_literals, print_function
from copy import copy
from email.mime.image import MIMEImage
import os
from datetime import datetime
import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from guests.models import Party


SAVE_THE_DATE_TEMPLATE = 'guests/email_templates/save_the_date.html'
SAVE_THE_DATE_CONTEXT_MAP = {
        'storm_and_elise': {
            'title': "Storm and Elise",
            'header_filename': 'hearts.png',
            'main_image': 'Elise-and-Storm-0037-cropped-min.jpg',
            'main_color': 'aliceblue',
            'font_color': '#666666',
        },
        'lions-head': {
            'title': "Lion's Head",
            'header_filename': 'hearts.png',
            'main_image': 'lions-head.jpg',
            'main_color': '#fff3e8',
            'font_color': '#666666',
        },
        'ski-trip': {
            'title': 'Ski Trip',
            'header_filename': 'hearts.png',
            'main_image': 'ski-trip.jpg',
            'main_color': '#330033',
            'font_color': '#ffffff',
        },
        'canada': {
            'title': 'Canada!',
            'header_filename': 'maple-leaf.png',
            'main_image': 'canada-cartoon-resized.jpg',
            'main_color': '#ea2e2e',
            'font_color': '#e5ddd9',
        },
        'american-gothic': {
            'title': 'American Gothic',
            'header_filename': 'hearts.png',
            'main_image': 'american-gothic.jpg',
            'main_color': '#b6ccb5',
            'font_color': '#000000',
        },
        'plunge': {
            'title': 'The Plunge',
            'header_filename': 'plunger.png',
            'main_image': 'plunge.jpg',
            'main_color': '#b4e6ff',
            'font_color': '#000000',
        },
        'dimagi': {
            'title': 'Dimagi',
            'header_filename': 'commcare.png',
            'main_image': 'join-us.jpg',
            'main_color': '#003d71',
            'font_color': '#d6d6d4',
        }
    }


def send_all_save_the_dates(test_only=False, mark_as_sent=False):
    to_send_to = Party.in_default_order().filter(is_invited=True, save_the_date_sent=None)
    for party in to_send_to:
        send_save_the_date_to_party(party, test_only=test_only)
        if mark_as_sent:
            party.save_the_date_sent = datetime.now()
            party.save()


def send_save_the_date_to_party(party, test_only=False):
    context = get_save_the_date_context(get_template_id_from_party(party))
    recipients = party.guest_emails
    if not recipients:
        print('===== WARNING: no valid email addresses found for {} ====='.format(party))
    else:
        send_save_the_date_email(
            context,
            recipients,
            test_only=test_only
        )


def get_template_id_from_party(party):
    return 'storm_and_elise'
    # if party.type == 'formal':
    #     # all formal guests get formal invites
    #     return random.choice(['lions-head', 'ski-trip'])
    # elif party.type == 'dimagi':
    #     # all non-formal dimagis get dimagi invites
    #     return 'dimagi'
    # elif party.type == 'fun':
    #     all_options = list(SAVE_THE_DATE_CONTEXT_MAP.keys())
    #     all_options.remove('dimagi')
    #     if party.category == 'ro':
    #         # don't send the canada invitation to ro's crowd
    #         all_options.remove('canada')
    #     # otherwise choose randomly from all options for everyone else
    #     return random.choice(all_options)
    # else:
    #     return None


def get_save_the_date_context(template_id):
    template_id = (template_id or '').lower()
    if template_id not in SAVE_THE_DATE_CONTEXT_MAP:
        template_id = 'storm_and_elise'
    context = copy(SAVE_THE_DATE_CONTEXT_MAP[template_id])
    context['name'] = template_id
    context['page_title'] = 'Storm Kaefer and Elise Tailleur - Save the Date!'
    context['couple'] = settings.GROOM_AND_BRIDE
    context['rsvp_address'] = settings.DEFAULT_WEDDING_REPLY_EMAIL
    context['site_url'] = settings.WEDDING_WEBSITE_URL
    context['preheader_text'] = (
        "{} are getting married! We would love for you to join us on our special day. "
        "Save the date!".format(settings.GROOM_AND_BRIDE_FULL)
    )
    return context


def send_save_the_date_email(context, recipients, test_only=False):
    context['email_mode'] = True
    template_html = render_to_string(SAVE_THE_DATE_TEMPLATE, context=context)
    template_text = "Save the date for {}'s wedding! December 28, 2019 in Edmonton, Alberta.".format(
        settings.GROOM_AND_BRIDE
    )
    subject = context.get('page_title')
    # https://www.vlent.nl/weblog/2014/01/15/sending-emails-with-embedded-images-in-django/
    msg = EmailMultiAlternatives(subject, template_text, settings.DEFAULT_WEDDING_FROM_EMAIL, recipients,
                                 reply_to=[settings.DEFAULT_WEDDING_REPLY_EMAIL])
    msg.attach_alternative(template_html, "text/html")
    msg.mixed_subtype = 'related'
    for filename in (context['header_filename'], context['main_image']):
        attachment_path = os.path.join(os.path.dirname(__file__), 'static', 'save-the-date', 'images', filename)
        with open(attachment_path, "rb") as image_file:
            msg_img = MIMEImage(image_file.read())
            msg_img.add_header('Content-ID', '<{}>'.format(filename))
            msg_img.add_header('Content-Disposition', "attachment; filename= %s" % context['couple'])
            msg.attach(msg_img)

    print('\nsending {} to {}\n'.format(context['name'], ', '.join(recipients)))
    if not test_only:
        msg.send()


def clear_all_save_the_dates():
    print('clear')
    for party in Party.objects.exclude(save_the_date_sent=None):
        party.save_the_date_sent = None
        print("resetting {}".format(party))
        party.save()
