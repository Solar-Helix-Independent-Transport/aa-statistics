from django.db import models
from allianceauth.eveonline.models import EveCharacter
from allianceauth.authentication.models import User

from . import filters as smart_filters

import datetime


class StatsCharacter(models.Model):
    character = models.OneToOneField(EveCharacter,
                                     on_delete=models.CASCADE,
                                     related_name='character_stats')
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
    last_update = models.DateTimeField(default=(datetime.datetime.utcnow() - datetime.timedelta(hours=9000)))

    zk_12m = models.IntegerField(default=0)
    zk_6m = models.IntegerField(default=0)
    zk_3m = models.IntegerField(default=0)

    def __str__(self):
        return self.character.character_name


class zKillMonth(models.Model):
    char = models.ForeignKey(StatsCharacter,
                             on_delete=models.CASCADE)
    year = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    ships_destroyed = models.IntegerField(default=0)
    ships_lost = models.IntegerField(default=0)
    isk_destroyed = models.BigIntegerField(default=0)
    isk_lost = models.BigIntegerField(default=0)
    last_update = models.DateTimeField(default=(datetime.datetime.utcnow() - datetime.timedelta(hours=9000)))

    def __str__(self):
        return self.char.character.character_name


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
