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
            party_pk, wedding_party_name, attended, gift, extra_sentence, send_a_thank_you_note = row[:6]
            if not party_pk:
                print('skipping row {}'.format(row))
                continue
            party = Party.objects.get(pk=party_pk)
            if gift:
                party.received_gifts = gift
            if extra_sentence:
                party.thank_you_extra_sentence = extra_sentence
            if send_a_thank_you_note == 'FALSE':
                party.receives_a_thank_you_note = False
            party.save()
        print('All Done!')
