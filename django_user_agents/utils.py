from hashlib import md5

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS
from user_agents import parse


try:
    from django.core.cache import caches
    def get_cache(backend, **kwargs):
        return caches[backend]

except ImportError:
    from django.core.cache import get_cache


USER_AGENTS_CACHE = getattr(settings, 'USER_AGENTS_CACHE', DEFAULT_CACHE_ALIAS)

if USER_AGENTS_CACHE:
    cache = get_cache(USER_AGENTS_CACHE)
else:
    cache = None


def get_cache_key(ua_string):
    # Some user agent strings are longer than 250 characters so we use its MD5
    if isinstance(ua_string, str):
        ua_string = ua_string.encode('utf-8')
    encoded = md5(ua_string.encode('utf-8')).hexdigest()
    return ''.join(['django_user_agents.', encoded])


def get_user_agent(request):
    # Tries to get UserAgent objects from cache before constructing a UserAgent
    # from scratch because parsing regexes.yaml/json (ua-parser) is slow
    if not hasattr(request, 'META'):
        return ''

    ua_string = request.META.get('HTTP_USER_AGENT', '')

    if not isinstance(ua_string, str):
        ua_string = ua_string.decode('utf-8', 'ignore')

    if cache:
        key = get_cache_key(ua_string)
        user_agent = cache.get(key)
        if user_agent is None:
            user_agent = parse(ua_string)
            cache.set(key, user_agent)
    else:
        user_agent = parse(ua_string)
    return user_agent


def get_and_set_user_agent(request):
    # If request already has ``user_agent``, it will return that, otherwise
    # call get_user_agent and attach it to request so it can be reused
    if hasattr(request, 'user_agent'):
        return request.user_agent

    if not request:
        return parse('')

    request.user_agent = get_user_agent(request)
    return request.user_agent
