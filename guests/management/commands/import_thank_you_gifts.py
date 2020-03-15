import csv

from django.core.management import BaseCommand

from guests.models import Party


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, filename, *args, **kwargs):
        import_thank_you_notes(filename)


def import_thank_you_notes(path):
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        first_row = True
        for row in reader:
            if first_row:
                first_row = False
                continue
            party_pk, party_name, attended, gift, extra_sentence, send_a_thank_you_note = row[:6]
            if not party_pk:
                print('skipping row {}'.format(row))
                continue
            try:
                party = Party.objects.get(pk=party_pk)
            except Party.DoesNotExist:
                print("Couldn't find party with pk {} and name {}.".format(party_pk, party_name))
                continue
            if gift and gift.strip():
                party.received_gifts = gift.strip()
            if extra_sentence and extra_sentence.strip():
                party.thank_you_extra_sentence = extra_sentence.strip()
            if send_a_thank_you_note == 'FALSE':
                party.receives_a_thank_you_note = False
            party.save()
        print('All Done!')
