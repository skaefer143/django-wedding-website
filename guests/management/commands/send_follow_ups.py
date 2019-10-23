from django.core.management import BaseCommand

from guests.follow_up import send_all_follow_ups


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--send',
            action='store_true',
            dest='send',
            default=False,
            help="Actually send emails"
        )
        parser.add_argument(
            '--mark-sent',
            action='store_true',
            dest='mark_sent',
            default=False,
            help="Mark as sent"
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help="Reset sent flags"
        )

    def handle(self, *args, **options):
        if options['reset']:
            raise NotImplementedError
        send_all_follow_ups(test_only=not options['send'], mark_as_sent=options['mark_sent'])
