from unittest import mock
from django.db.models.query_utils import Q
from django.test import TestCase
from allianceauth.tests.auth_utils import AuthUtils
from allianceauth.eveonline.models import EveCharacter
from allianceauth.authentication.models import CharacterOwnership
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from . import filters
from .models import zKillStatsFilter
from aastatistics import models as a_models
from django.contrib.auth.models import User, Group

from aastatistics import models


class TestGroupBotFilters(TestCase):
    @classmethod
    def setUpTestData(cls):

        EveCharacter.objects.all().delete()
        User.objects.all().delete()
        CharacterOwnership.objects.all().delete()
        a_models.StatsCharacter.objects.all().delete()
        a_models.zKillMonth.objects.all().delete()
        
        userids = range(1,11)
        
        users = []
        characters = []
        for uid in userids:
            user = AuthUtils.create_user(f"User_{uid}")
            main_char = AuthUtils.add_main_character_2(user,
                                                       f"Main {uid}",
                                                       uid,
                                                       corp_id=1,
                                                       corp_name='Test Corp 1',
                                                       corp_ticker='TST1')
            CharacterOwnership.objects.create(user=user, character=main_char, owner_hash=f"main{uid}")

            characters.append(main_char)                                      
            users.append(user)

        # add some extra characters to users in 2 corps/alliance
        for uid in range(0,5): # test corp 2
            character = EveCharacter.objects.create(character_name=f'Alt {uid}', 
                                                    character_id=11+uid, 
                                                    corporation_name='Test Corp 2', 
                                                    corporation_id=2, 
                                                    corporation_ticker='TST2')
            CharacterOwnership.objects.create(character=character, 
                                              user=users[uid], 
                                              owner_hash=f'ownalt{11+uid}')
            characters.append(character)

        for uid in range(5,10): # Test alliance 1
            character = EveCharacter.objects.create(character_name=f'Alt {uid}', 
                                                    character_id=11+uid, 
                                                    corporation_name='Test Corp 3', 
                                                    corporation_id=3, 
                                                    corporation_ticker='TST3',
                                                    alliance_id=1,
                                                    alliance_name="Test Alliance 1",
                                                    alliance_ticker="TSTA1")
            CharacterOwnership.objects.create(character=character, 
                                              user=users[uid], 
                                              owner_hash=f'ownalt{11+uid}')
            characters.append(character)

        zkc = a_models.StatsCharacter.objects.create(character=characters[2],
                                                  zk_12m=500, zk_6m=250, zk_3m=100)
        zkc2 = a_models.StatsCharacter.objects.create(character=characters[4],
                                                  zk_12m=0, zk_6m=0, zk_3m=0)

        date_str= str(timezone.now().year)+str(timezone.now().month).zfill(2)
        a_models.zKillMonth.objects.create(char=zkc2, ships_destroyed=5, date_str=date_str, month=timezone.now().month, year=timezone.now().year)

    def test_user_zkill_pre_calc_12(self):
        users = {}
        for user in User.objects.all():
            users[user.pk] = None

        tests = {}
        for k,u in users.items():
            tests[k] = filters.check_kills_in_account(User.objects.get(pk=k), 12, 499)
        self.assertFalse(tests[1])
        self.assertFalse(tests[2])
        self.assertTrue(tests[3])
        self.assertFalse(tests[4])
        self.assertFalse(tests[5])
        self.assertFalse(tests[6])
        self.assertFalse(tests[7])
        self.assertFalse(tests[8])
        self.assertFalse(tests[9])
        self.assertFalse(tests[10])

    def test_user_zkill_pre_calc_6(self):
        users = {}
        for user in User.objects.all():
            users[user.pk] = None
                    
        tests = {}
        for k,u in users.items():
            tests[k] = filters.check_kills_in_account(User.objects.get(pk=k), 6, 249)
            
        self.assertFalse(tests[1])
        self.assertFalse(tests[2])
        self.assertTrue(tests[3])
        self.assertFalse(tests[4])
        self.assertFalse(tests[5])
        self.assertFalse(tests[6])
        self.assertFalse(tests[7])
        self.assertFalse(tests[8])
        self.assertFalse(tests[9])
        self.assertFalse(tests[10])

    def test_user_zkill_pre_calc_3(self):
        users = {}
        for user in User.objects.all():
            users[user.pk] = None
                    
        tests = {}
        for k,u in users.items():
            tests[k] = filters.check_kills_in_account(User.objects.get(pk=k), 3, 99)
            
        self.assertFalse(tests[1])
        self.assertFalse(tests[2])
        self.assertTrue(tests[3])
        self.assertFalse(tests[4])
        self.assertFalse(tests[5])
        self.assertFalse(tests[6])
        self.assertFalse(tests[7])
        self.assertFalse(tests[8])
        self.assertFalse(tests[9])
        self.assertFalse(tests[10])

    def test_user_zkill_calc(self):
        users = {}
        for user in User.objects.all():
            users[user.pk] = None
                    
        tests = {}
        for k,u in users.items():
            tests[k] = filters.check_kills_in_account(User.objects.get(pk=k), 2, 4)
            
        self.assertFalse(tests[1])
        self.assertFalse(tests[2])
        self.assertFalse(tests[3])
        self.assertFalse(tests[4])
        self.assertTrue(tests[5])
        self.assertFalse(tests[6])
        self.assertFalse(tests[7])
        self.assertFalse(tests[8])
        self.assertFalse(tests[9])
        self.assertFalse(tests[10])

    def test_user_zkill_audit(self):
        users = []

        for user in User.objects.all():
            users.append(user.pk)

        s_filter = zKillStatsFilter.objects.create(name="3/99",description="3/99",
                                                    months=2, kill_count=4)

        tests = s_filter.audit_filter(User.objects.filter(id__in=users))

        self.assertFalse(tests[1]['check'])
        self.assertFalse(tests[2]['check'])
        self.assertFalse(tests[3]['check'])
        self.assertFalse(tests[4]['check'])
        self.assertTrue(tests[5]['check'])
        self.assertFalse(tests[6]['check'])
        self.assertFalse(tests[7]['check'])
        self.assertFalse(tests[8]['check'])
        self.assertFalse(tests[9]['check'])
        self.assertFalse(tests[10]['check'])
