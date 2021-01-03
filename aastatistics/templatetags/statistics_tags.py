from django import template
from django.db.models import Sum
from django.db.models.functions import Coalesce
from math import floor

import datetime

from aastatistics.models import StatsCharacter, zKillMonth
from allianceauth.eveonline.models import EveCharacter

register = template.Library()


@register.filter(name='get_ytd_kills_single')
def get_ytd_kills_single(input_id, month=None):
    try:
        now = datetime.datetime.now()

        month_12_ago = ((now.month - 1 - 12) % 12 + 1)
        month_6_ago = ((now.month - 1 - 6) % 12 + 1)
        month_3_ago = ((now.month - 1 - 3) % 12 + 1)
        year_12_ago = (now.year + floor((now.month - 12) / 12))
        year_6_ago = (now.year + floor((now.month - 6) / 12))
        year_3_ago = (now.year + floor((now.month - 3) / 12))

        character = StatsCharacter.objects.filter(character__character_id=input_id)

        qs = zKillMonth.objects.filter(char__in=character)

        qs_12m = qs.filter(year=year_12_ago, month__gte=month_12_ago) | \
                 qs.filter(year=now.year)
        qs_12m = qs_12m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        qs_6m = qs.filter(year=year_6_ago, month__gte=month_6_ago)
        if now.month < 6:
            qs_6m = qs_6m | qs.filter(year=now.year)
        qs_6m = qs_6m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        qs_3m = qs.filter(year__gte=year_3_ago, month__gte=month_3_ago)
        if now.month < 3:
            qs_3m = qs_3m | qs.filter(year=now.year)
        qs_3m = qs_3m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % \
               (str(qs_12m if qs_12m else 0), str(qs_6m if qs_6m else 0), str(qs_3m if qs_3m else 0))

    except:
        return "<td class=\"text-center\">%s</td><td class=\"text-center\">%s</td><td class=\"text-center\">%s</td>" % (str(0), str(0), str(0))


@register.filter(name='get_ytd_kills_account')
def get_ytd_kills_account(input_id):
    try:
        now = datetime.datetime.now()

        in_char = EveCharacter.objects.get(character_id=input_id).character_ownership.user.profile.main_character
        character_list = in_char.character_ownership.user.character_ownerships.all().select_related('character')
        character_ids = set(character_list.values_list('character__character_id', flat=True))

        month_12_ago = ((now.month - 1 - 12) % 12 + 1)
        month_6_ago = ((now.month - 1 - 6) % 12 + 1)
        month_3_ago = ((now.month - 1 - 3) % 12 + 1)
        year_12_ago = (now.year + floor((now.month - 12) / 12))
        year_6_ago = (now.year + floor((now.month - 6) / 12))
        year_3_ago = (now.year + floor((now.month - 3) / 12))

        character = StatsCharacter.objects.filter(character__character_id__in=character_ids)

        qs = zKillMonth.objects.filter(char__in=character)

        qs_12m = qs.filter(year=year_12_ago, month__gte=month_12_ago) | \
                 qs.filter(year=now.year)
        qs_12m = qs_12m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        qs_6m = qs.filter(year=year_6_ago, month__gte=month_6_ago)
        if now.month<6:
            qs_6m = qs_6m | qs.filter(year=now.year)
        qs_6m = qs_6m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        qs_3m = qs.filter(year__gte=year_3_ago, month__gte=month_3_ago)
        if now.month < 3:
            qs_3m = qs_3m | qs.filter(year=now.year)
        qs_3m = qs_3m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % \
               (str(qs_12m if qs_12m else 0), str(qs_6m if qs_6m else 0), str(qs_3m if qs_3m else 0))

    except:
        return "<td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td><td class=\"text-center\" style=\"vertical-align:middle\">%s</td>" % (str(0), str(0), str(0))
