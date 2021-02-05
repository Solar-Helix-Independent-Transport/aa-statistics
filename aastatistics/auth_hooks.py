from allianceauth.services.hooks import UrlHook
from allianceauth import hooks
from .models import zKillStatsFilter
from . import urls


@hooks.register('url_hook')
def register_url():
    return UrlHook(urls, 'aastatistics', r'^aastatistics/')

@hooks.register("secure_group_filters")
def filters():
    return [zKillStatsFilter]