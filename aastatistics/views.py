import csv
from django.http import HttpResponse
from .tasks import output_stats
from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required('corputils.view_alliance_corpstats')
def outputcsv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="auth_zkill_dump.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Corp', '12m', '6m', '3m'])
    for char, data in output_stats(file_output=False).items():
        writer.writerow(data)

    return response
