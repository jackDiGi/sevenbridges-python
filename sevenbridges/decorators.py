import functools
import json
import requests

from sevenbridges.errors import (
    BadRequest, Unauthorized, Forbidden, NotFound, MethodNotAllowed,
    RequestTimeout, Conflict, TooManyRequests, SbgError
)


def inplace_reload(method):
    """
    Executes the wrapped function and reloads the object
    with data returned from the server.
    """

    # noinspection PyProtectedMember
    def wrapped(obj, *args, **kwargs):
        in_place = True if kwargs.get('inplace') in (True, None) else False
        api_object = method(obj, *args, **kwargs)
        if in_place and api_object:
            obj._data = api_object._data
            obj._compound_cache = api_object._compound_cache
            obj._dirty = api_object._dirty
            return obj
        elif api_object:
            return api_object
        else:
            return obj

    return wrapped


def check_for_error(func):
    """
    Executes the wrapped function and inspects the response object
    for specific errors.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            status_code = response.status_code
            if status_code in range(200, 204):
                return response
            if status_code == 204:
                return
            data = response.json()
            e = {
                400: BadRequest,
                401: Unauthorized,
                403: Forbidden,
                404: NotFound,
                405: MethodNotAllowed,
                408: RequestTimeout,
                409: Conflict,
                429: TooManyRequests,
            }.get(status_code, SbgError)()
            if 'message' in data:
                e.message = data['message']
            if 'code' in data:
                e.code = data['code']
            if 'status' in data:
                e.status = data['status']
            if 'more_info' in data:
                e.more_info = data['more_info']
            raise e
        except requests.RequestException as e:
            raise SbgError(message=str(e))
        except ValueError as e:
            raise SbgError(message=str(e))

    return wrapper
