from django.db.models import Sum
from django.db.models.functions import Coalesce
from dateutil.relativedelta import relativedelta

import datetime

import logging

logger = logging.getLogger(__name__)


def check_kills_in_account(user, months, kills):
    from .models import StatsCharacter, zKillMonth
    """
    Check Account for x Kills for x months
 
    Parameters
    ==========
    user (model)
    Months (int)
    Kills (int)

    Returns
    ======
    Returns True/False
    """
    try:
        logger.debug("Checking kills for {0}, in the last {1} months, {2} kill threshold.".format(user.profile.main_character.character_name, months, kills))

        now = datetime.datetime.now()
        character_list = user.character_ownerships.all().select_related('character', 'character__character_stats')
        if months == 12:
            kill_count = 0
            for c in character_list:
                try:
                    kill_count += c.character.character_stats.zk_12m
                except Exception as e:
                    logger.error(e)
                    pass       
        elif months == 6:
            kill_count = 0
            for c in character_list:
                try:
                    kill_count += c.character.character_stats.zk_6m
                except Exception as e:
                    logger.error(e)
                    pass
        elif months == 3:
            kill_count = 0
            for c in character_list:
                try:
                    kill_count += c.character.character_stats.zk_3m
                except Exception as e:
                    logger.error(e)
                    pass
        else:
            character_ids = set(character_list.values_list('character__character_id', flat=True))

            dt = now - relativedelta(months=months)
            month_ago = dt.month
            year_ago = dt.year

            characters = StatsCharacter.objects.filter(character__character_id__in=character_ids)

            qs = zKillMonth.objects.filter(char__in=characters)

            qs_kills = qs.filter(year__gte=year_ago, month__gte=month_ago)
            if year_ago < now.year:
                qs_kills = qs_kills | qs.filter(year=now.year)

            kill_count = qs_kills.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)

        # logger.debug(kill_count)
        if kill_count >= kills:
            return True
        else:
            return False
    except:
        return False
