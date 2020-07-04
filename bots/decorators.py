from functools import wraps

from rumors.utils import respect_language


def bot_respects_user_language(fun):
    @wraps(fun)
    def _inner(*args, **kwargs):
        with respect_language(args[0].from_user.language_code):
            return fun(*args, **kwargs)

    return _inner


def arabic_only(fun):
    @wraps(fun)
    def _inner(*args, **kwargs):
        with respect_language('ar'):
            return fun(*args, **kwargs)

    return _inner
