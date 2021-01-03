from django.conf import settings

MEMBER_ALLIANCES = getattr(settings, "MEMBER_ALLIANCES", [])
