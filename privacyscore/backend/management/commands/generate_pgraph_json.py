from django.core.management.base import BaseCommand, CommandError
import json
from django.core.serializers.json import DjangoJSONEncoder
from privacyscore.backend.models import Scan, Site, RawScanResult, ScanResult



class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('start', type=int, help='start index')
        parser.add_argument('end', type=int, help='end')


    def handle(self, *args, **kwargs):
        if kwargs['end']-kwargs['start'] > 300:
            return "Nicht mehr als 300 auf einmal"

        if kwargs['end'] > ScanResult.objects.all().count():
            return "Es sind nur " + str(ScanResult.objects.all().count()) + 'Scan Ergebnisse in der Datenbank'

        if kwargs['end'] - kwargs['end'] < 0:
            return 'start und ende vertauscht'
        # collect Scans

        srs = ScanResult.objects.all().order_by('id')[kwargs['start']:kwargs['end']+1]

        # create list
        result = []
        for sr in srs:
            data = {'third_parties': sr.result.get('third_parties'), 'cookie_stats': sr.result.get('cookie_stats'),
                    'initial_url': sr.scan.site.url}
            final_string = {'date': str(sr.scan.start), 'id': sr.id, 'data': data}
            result.append(final_string)
        print(json.dumps(result,  cls=DjangoJSONEncoder))



