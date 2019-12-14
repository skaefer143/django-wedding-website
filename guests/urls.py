from django.conf.urls import url

from guests.views import GuestListView, test_email, save_the_date_preview, save_the_date_random, export_guests, \
    invitation, invitation_email_preview, invitation_email_test, rsvp_confirm, dashboard, save_the_date_redirect, \
    follow_up_email_preview, follow_up_email_test, reminder_email_preview, reminder_email_test

urlpatterns = [
    url(r'^guests/$', GuestListView.as_view(), name='guest-list'),
    url(r'^dashboard/$', dashboard, name='dashboard'),
    url(r'^guests/export$', export_guests, name='export-guest-list'),
    url(r'^invite/(?P<invite_id>[\w-]+)/$', invitation, name='invitation'),
    url(r'^invite-email/(?P<invite_id>[\w-]+)/$', invitation_email_preview, name='invitation-email'),
    url(r'^invite-email-test/(?P<invite_id>[\w-]+)/$', invitation_email_test, name='invitation-email-test'),
    url(r'^follow-up-email/(?P<invite_id>[\w-]+)/$', follow_up_email_preview, name='follow-up-email'),
    url(r'^follow-up-email-test/(?P<invite_id>[\w-]+)/$', follow_up_email_test, name='follow-up-email-test'),
    url(r'^reminder-email/(?P<invite_id>[\w-]+)/$', reminder_email_preview, name='follow-up-email'),
    url(r'^reminder-email-test/(?P<invite_id>[\w-]+)/$', reminder_email_test, name='follow-up-email-test'),
    url(r'^save-the-date/$', save_the_date_random, name='save-the-date-random'),
    url(r'^save-the-date/(?P<template_id>[\w-]+)/$', save_the_date_preview, name='save-the-date'),
    url(r'^save-the-date-redirect/(?P<save_the_date_id>[\w-]+)/$', save_the_date_redirect, name='save-the-date-redirect'),
    url(r'^email-test/(?P<template_id>[\w-]+)/$', test_email, name='test-email'),
    url(r'^rsvp/confirm/(?P<invite_id>[\w-]+)/$', rsvp_confirm, name='rsvp-confirm'),
]
