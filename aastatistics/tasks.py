import logging
import requests
import datetime
import csv

from celery import shared_task, chain

from .models import StatsCharacter, zKillMonth
from allianceauth.eveonline.models import EveCharacter
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from time import sleep
from math import floor
from allianceauth.services.tasks import QueueOnce
from . import app_settings

logger = logging.getLogger(__name__)

if apps.is_installed("allianceauth.corputils"):
    from allianceauth.corputils.models import CorpStats
elif apps.is_installed("corpstats"):
    from corpstats.models import CorpStat as CorpStats
else:
    pass


def update_character_stats(character_id):
    #logger.info('update_character_stats for %s starting' % str(character_id))
    # https://zkillboard.com/api/stats/characterID/####/
    _stats_request = requests.get("https://zkillboard.com/api/stats/characterID/" + str(character_id) + "/")
    _stats_json = _stats_request.json()
    sleep(1)

    _last_kill_date = None

    char_model, created = StatsCharacter.objects.get_or_create(character=EveCharacter.objects.get(character_id=int(character_id)))

    if len(_stats_json.get('months', [])) > 0:
        current_data = zKillMonth.objects.filter(char=char_model)
        years = {}

        for m in current_data:
            if m.year not in years:
                years[m.year]={}
            years[m.year][m.month]=m
        
        updates = []
        creates = []
        for key, month in _stats_json.get('months', []).items(): 
            new_model = False
            try:
                zkill_month = years[month.get('year')][month.get('month')]
            except KeyError as e:
                zkill_month = zKillMonth(char=char_model, year=month.get('year', 0), month=month.get('month', 0))
                new_model = True
            zkill_month.date_str = str(month.get('year'))+str(month.get('month')).zfill(2)
            zkill_month.ships_destroyed = month.get('shipsDestroyed', 0)
            zkill_month.ships_lost = month.get('shipsLost', 0)
            zkill_month.isk_destroyed = month.get('iskDestroyed', 0)
            zkill_month.isk_lost = month.get('iskLost', 0)
            zkill_month.last_update = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            if new_model:
                creates.append(zkill_month)
            else:
                updates.append(zkill_month)
        
        if len(updates) > 0:
            zKillMonth.objects.bulk_update(updates, batch_size=500, fields=['ships_destroyed', 'ships_lost', 'isk_destroyed', 'isk_lost', 'last_update', 'date_str'])
        if len(creates) > 0:
            zKillMonth.objects.bulk_create(creates, batch_size=500)

    char_model.isk_destroyed = _stats_json.get('iskDestroyed', 0)
    char_model.isk_lost = _stats_json.get('iskLost', 0)
    char_model.all_time_sum = _stats_json.get('allTimeSum', 0)
    char_model.gang_ratio = _stats_json.get('gangRatio', 0)
    char_model.ships_destroyed = _stats_json.get('shipsDestroyed', 0)
    char_model.ships_lost = _stats_json.get('shipsLost', 0)
    char_model.solo_destroyed = _stats_json.get('soloDestroyed', 0)
    char_model.solo_lost = _stats_json.get('soloLost', 0)
    char_model.active_pvp_kills = _stats_json.get('activepvp', {}).get('kills', {}).get('count', 0)
    char_model.last_kill = _last_kill_date
    char_model.last_update = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
    char_model.save()

    #logger.info('update_character_stats for %s complete' % str(character_id))

@shared_task(bind=True, base=QueueOnce)
def update_char(self, char_id):
    try:
        now = datetime.datetime.now()
        skip_time =  timezone.now() - relativedelta(hours=24)
        dt12 = now - relativedelta(months=12)
        dt6 = now - relativedelta(months=6)
        dt3 = now - relativedelta(months=3)
        try:
            #logger.info('update_character_stats for %s starting' % str(char_id))
            update_character_stats(char_id)
        except:
            logger.error('update_character_stats failed for %s' % str(char_id))
            logging.exception("Messsage")
            sleep(1)  # had an error printed it and skipped it YOLO. better wait a sec to not overload the api
            return 0 # fail
        try:
            character = StatsCharacter.objects.get(character__character_id=char_id)
            qs = zKillMonth.objects.filter(char=character)
            qs_12m = qs.filter(year=dt12.year, month__gte=dt12.month) | \
                        qs.filter(year=now.year)
            qs_12m = qs_12m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_6m = qs.filter(year=dt6.year, month__gte=dt6.month)
            if now.month <= 6:
                qs_6m = qs_6m | qs.filter(year=now.year)
            qs_6m = qs_6m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            qs_3m = qs.filter(year__gte=dt3.year, month__gte=dt3.month)
            if now.month <= 3:
                qs_3m = qs_3m | qs.filter(year=now.year)
            qs_3m = qs_3m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
            character.zk_12m = qs_12m
            character.zk_6m = qs_6m
            character.zk_3m = qs_3m
            character.save()
        except ObjectDoesNotExist:
            pass # broken

    except Exception as e:
        logger.error("failed to update {}: {}".format(char_id, e))
        return 0  # fail
    
    return 1  # pass


@shared_task()
def run_stat_model_update():
    # update all corpstat'd characters
    #logger.info('start')
    member_alliances = app_settings.MEMBER_ALLIANCES
    linked_chars = EveCharacter.objects.filter(alliance_id__in=member_alliances)  # get all authenticated characters in corp from auth internals

    sig_list = []

    for alt in linked_chars:
        if alt.alliance_id in member_alliances:
            sig_list.append(update_char.si(alt.character_id))

    chain(sig_list).apply_async(priority=8)


@shared_task()
def run_aggregate_update():
    # update all corpstat'd characters
    #logger.info('start')
    active_corp_stats = CorpStats.objects.all()
    member_alliances = app_settings.MEMBER_ALLIANCES
    now = datetime.datetime.now()
    dt12 = now - relativedelta(months=12)
    dt6 = now - relativedelta(months=6)
    dt3 = now - relativedelta(months=3)
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            for alt in member.alts:
                if alt.alliance_id in member_alliances:
                    try:
                        logger.info('update_character_agregates for %s starting' % str(alt.character_name))
                        character = StatsCharacter.objects.get(character__character_id=alt.character_id)
                        qs = zKillMonth.objects.filter(char=character)
                        qs_12m = qs.filter(year=dt12.year, month__gte=dt12.month) | \
                                 qs.filter(year=now.year)
                        qs_12m = qs_12m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
                        qs_6m = qs.filter(year=dt6.year, month__gte=dt6.month)
                        if now.month <= 6:
                            qs_6m = qs_6m | qs.filter(year=now.year)
                        qs_6m = qs_6m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
                        qs_3m = qs.filter(year__gte=dt3.year, month__gte=dt3.month)
                        if now.month <= 3:
                            qs_3m = qs_3m | qs.filter(year=now.year)
                        qs_3m = qs_3m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get('ship_destroyed_sum', 0)
                        character.zk_12m = qs_12m
                        character.zk_6m = qs_6m
                        character.zk_3m = qs_3m
                        character.save()
                    except ObjectDoesNotExist:
                        logger.info('failed update_character_agregates for %s starting' % str(alt.character_name))
                        pass # who knows    

def output_stats(file_output=True):
    active_corp_stats = CorpStats.objects.all()

    out_arr={}
    for cs in active_corp_stats:
        members = cs.mains
        for member in members:
            print("Adding: %s" % member.character.character_name)
            now = datetime.datetime.now()
            #try:
            in_char = EveCharacter.objects.get(
                character_id=member.character.character_id).character_ownership.user.profile.main_character
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
            qs_12m = qs_12m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                'ship_destroyed_sum', 0)

            qs_6m = qs.filter(year=year_6_ago, month__gte=month_6_ago)
            if now.month < 6:
                qs_6m = qs_6m | qs.filter(year=now.year)
            qs_6m = qs_6m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                'ship_destroyed_sum', 0)

            qs_3m = qs.filter(year__gte=year_3_ago, month__gte=month_3_ago)
            if now.month < 3:
                qs_3m = qs_3m | qs.filter(year=now.year)
            qs_3m = qs_3m.aggregate(ship_destroyed_sum=Coalesce(Sum('ships_destroyed'), 0)).get(
                'ship_destroyed_sum', 0)

            out_str=[]
            out_str.append(in_char.character_name)
            out_str.append(in_char.corporation_name)
            out_str.append(str(qs_12m))
            out_str.append(str(qs_6m))
            out_str.append(str(qs_3m))
            out_arr[in_char.character_name]=out_str
            #except:
             #   pass
    
    if file_output:
        with open('auth_zkill_dump.csv', 'w') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerow(['Name', 'Corp', '12m', '6m', '3m'])
            for char, data in out_arr.items():
                writer.writerow(data)
        writeFile.close()
    else:
        return out_arr
    
