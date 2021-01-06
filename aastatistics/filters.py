from django.db.models import Sum
from django.db.models.functions import Coalesce
from dateutil.relativedelta import relativedelta
from allianceauth.authentication.models import CharacterOwnership
import datetime

import logging
logger = logging.getLogger(__name__)

try:
    from aastatistics.models import StatsCharacter, zKillMonth
except ImportError:
    logger.error("Cannot Load AA Statistics module. Is it installed?")


def check_kills_in_account(user, months, kills):
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
    logger.debug("Checking kills for {0}, in the last {1} months, {2} kill threshold.".format(user.main_character.character_name, months, kills))

    try:
        now = datetime.datetime.now()
        character_list = CharacterOwnership.get(user=user).character.all().select_related('character', 'character__character_stats')
        exempt = character_list.filter(character__group_bot_exemptions__kill_exempt=True).count()
        if exempt == 0:
            if months == 12:
                kill_count = 0
                for c in character_list:
                    try:
                        kill_count += c.character.zkill.zk_12m
                    except Exception as e:
                        logger.error(e)
                        pass
            else:
                character_ids = set(character_list.values_list('character__character_id', flat=True))

                dt = now - relativedelta(months=months)
                month_ago = dt.month
                year_ago = dt.year

                character = StatsCharacter.objects.filter(character__character_id__in=character_ids)

                qs = zKillMonth.objects.filter(char__in=character)

                qs_kills = qs.filter(year__gte=year_ago, month__gte=month_ago)
                if year_ago < now.year:
                    qs_kills = qs_kills | qs.filter(year=now.year)

                kill_count = qs_kills.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
  
            # logger.debug(kill_count)
            if kill_count >= kills:
                return True
            else:
                return False
        return True
    except:
        return False
