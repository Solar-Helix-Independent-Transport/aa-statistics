from django.db import models
from allianceauth.eveonline.models import EveCharacter
from allianceauth.authentication.models import User
from allianceauth.authentication.models import CharacterOwnership
from django.db.models import Max, Sum, Q
from . import filters as smart_filters
from collections import defaultdict
from dateutil.relativedelta import relativedelta

import datetime


class StatsCharacter(models.Model):
    character = models.OneToOneField(EveCharacter, on_delete=models.CASCADE, related_name='character_stats')
    isk_destroyed = models.BigIntegerField(default=0)
    isk_lost = models.BigIntegerField(default=0)
    all_time_sum = models.IntegerField(default=0)
    gang_ratio = models.IntegerField(default=0)
    ships_destroyed = models.IntegerField(default=0)
    ships_lost = models.IntegerField(default=0)
    solo_destroyed = models.IntegerField(default=0)
    solo_lost = models.IntegerField(default=0)
    active_pvp_kills = models.IntegerField(default=0)
    last_kill = models.DateTimeField(null=True, default=None)
    last_update = models.DateTimeField(default=datetime.datetime.min)

    zk_12m = models.IntegerField(default=0)
    zk_6m = models.IntegerField(default=0)
    zk_3m = models.IntegerField(default=0)

    def __str__(self):
        return self.character.character_name


class zKillMonth(models.Model):
    char = models.ForeignKey(StatsCharacter, on_delete=models.CASCADE)
    year = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    date_str = models.CharField(max_length=6)
    ships_destroyed = models.IntegerField(default=0)
    ships_lost = models.IntegerField(default=0)
    isk_destroyed = models.BigIntegerField(default=0)
    isk_lost = models.BigIntegerField(default=0)
    last_update = models.DateTimeField(default=datetime.datetime.min)

    def __str__(self):
        return self.char.character.character_name

    class Meta:
        indexes = [
            models.Index(fields=['date_str']),
            models.Index(fields=['year']),
            models.Index(fields=['month']),
        ]


class FilterBase(models.Model):

    name = models.CharField(max_length=500)
    description = models.CharField(max_length=500)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name}: {self.description}"

    def process_filter(self, user: User):
        raise NotImplementedError("Please Create a filter!")


class zKillStatsFilter(FilterBase):
    class Meta:
        verbose_name = "Smart Filter: zKill: Kills in Period"
        verbose_name_plural = verbose_name

    kill_count = models.IntegerField(default=0)
    months = models.IntegerField(default=1)

    def process_filter(self, user: User):
        return smart_filters.check_kills_in_account(
            user, self.months, self.kill_count
        )


    def audit_filter(self, users):
        now = datetime.datetime.now()
        dt = now - relativedelta(months=self.months)
        date_str = str(dt.year)+str(dt.month).zfill(2)

        _cos = CharacterOwnership.objects.filter(user__in=users).annotate(
            kills=Sum('character__character_stats__zkillmonth__ships_destroyed',
                      filter=Q(character__character_stats__zkillmonth__date_str__gte=date_str)
                )
            ).values("user_id", 'character_id', "kills")
        
        co = {}
        for c in _cos:
            u = c.get('user_id')
            if u not in co:
                co[u] = 0
            if c.get('kills'):
                co[u] += c.get('kills')

        output = defaultdict(lambda: {"message": "", "check": False})
        for u, c in co.items():
            if c:
                if c >= self.kill_count:
                    check = True
                else:
                    check = False
                msg = str(c) + " Kills"
            else:
                check = False
                msg = "0 Kill Data"

            output[u] = {"message": msg, "check": check}
        return output
