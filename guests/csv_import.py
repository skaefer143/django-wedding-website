import csv
import io
from guests.models import Party, Guest, _random_uuid

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def import_guests(path):
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        first_row = True
        for row in reader:
            if first_row:
                first_row = False
                continue
            party_name, first_name, last_name, category, is_invited, is_attending, email, notes = row[:8]
            if not party_name:
                print ('skipping row {}'.format(row))
                continue
            party, party_created = Party.objects.get_or_create(name=party_name)
            party.category = category
            party.is_invited = _is_true(is_invited)
            party.is_attending = _is_null_or_true(is_attending)
            if not party.invitation_id:
                party.invitation_id = _random_uuid()
            if not party.save_the_date_id:
                party.save_the_date_id = _random_uuid()
            if party_created:
                print('Adding Party {}'.format(party_name))
            party.save()
            if email:
                guest, guest_created = Guest.objects.get_or_create(party=party, email=email)
                guest.first_name = first_name
                guest.last_name = last_name
            else:
                guest, guest_created = Guest.objects.get_or_create(party=party, first_name=first_name, last_name=last_name)

            if guest_created:
                print('Adding Guest {} {}'.format(guest.first_name, guest.last_name))
            guest.notes = notes
            guest.is_attending = _is_null_or_true(is_attending)
            guest.save()
        print('All Done!')


def export_guests():
    headers = [
        'party_name', 'first_name', 'last_name', 'category',
        'is_invited', 'is_attending', 'rehearsal_dinner', 'email', 'notes'
    ]
    file = io.StringIO()
    writer = csv.writer(file)
    writer.writerow(headers)
    for party in Party.in_default_order():
        for guest in party.guest_set.all():
            if guest.is_attending:
                writer.writerow([
                    party.name,
                    guest.first_name,
                    guest.last_name,
                    party.category,
                    party.is_invited,
                    guest.is_attending,
                    party.rehearsal_dinner,
                    guest.email,
                    guest.notes,
                ])
    return file


def _is_true(value):
    value = value or ''
    return value.lower() in ('y', 'yes')


def _is_null_or_true(value):
    value = value or ''
    if value == '':
        return None
    return value.lower() in ('y', 'yes')
