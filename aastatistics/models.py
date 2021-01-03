from django.db import models
from allianceauth.eveonline.models import EveCharacter

import datetime


class StatsCharacter(models.Model):
    character = models.OneToOneField(EveCharacter,
                                     on_delete=models.CASCADE,
                                     related_name='zkill')
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
