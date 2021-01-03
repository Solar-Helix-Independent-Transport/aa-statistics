from allianceauth.services.hooks import UrlHook
from allianceauth import hooks
from . import urls


@hooks.register('url_hook')
def register_url():
    return UrlHook(urls, 'aastatistics', r'^aastatistics/')
