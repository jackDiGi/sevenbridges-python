import json
import platform
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util import Retry
from sevenbridges.errors import SbgError
from sevenbridges.decorators import check_for_error
import sevenbridges

client_info = {
    'version': sevenbridges.__version__,
    'os': platform.system(),
    'python': platform.python_version(),
    'requests': requests.__version__,

}


class HttpClient(object):
    """
    Implementation of all low-level API stuff, creating and sending requests,
    returning raw responses, authorization, etc.
    """

    def __init__(self, url=None, token=None, oauth_token=None, config=None,
                 timeout=None, retry=5):

        if config is not None:
            url = config.api_url
            token = config.auth_token
            oauth_token = config.oauth_token

        if not url:
            raise SbgError(message="Url is missing!")

        self.url = url.rstrip('/')
        self._session = requests.Session()
        self._session.mount(self.url, HTTPAdapter(
            max_retries=Retry(total=retry, status_forcelist=[500, 503])
        ))
        self.timeout = timeout
        self._limit = None
        self._remaining = None
        self._reset = None
        self._request_id = None
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent':
                'sevenbridges-python/{version} ({os}, Python/{python}; '
                'requests/{requests})'.format(**client_info)
        }
        self.timeout = timeout
        self.token = token
        self.oauth_token = oauth_token
        if self.token:
            self.headers['X-SBG-Auth-Token'] = token
        elif self.oauth_token:
            self.headers['Authorization'] = 'Bearer {}'.format(oauth_token)
        else:
            raise SbgError(
                message='Required authorization model not selected!. Please '
                        'provide at least one token value.'
            )

    @property
    def session(self):
        return self._session

    @property
    def limit(self):
        return self._limit

    @property
    def remaining(self):
        return self._remaining

    @property
    def reset_time(self):
        return self._reset

    @property
    def request_id(self):
        return self._request_id

    @check_for_error
    def _request(self, verb, url, headers=None, params=None, data=None,
                 append_base=False, stream=False):
        if append_base:
            url = self.url + url
        if not headers:
            headers = self.headers
        else:
            headers = headers.update(self.headers)
        if not self.token or self.oauth_token:
            raise SbgError(message="Api instance must be authenticated.")
        if not stream:
            response = self._session.request(
                verb, url, params=params, data=json.dumps(data),
                headers=headers, timeout=self.timeout, stream=stream
            )
        else:
            response = self._session.request(
                verb, url, params=params, stream=stream
            )
        headers = response.headers
        self._limit = headers.get('X-RateLimit-Limit', self._limit)
        self._remaining = headers.get('X-RateLimit-Remaining', self._remaining)
        self._reset = headers.get('X-RateLimit-Reset', self._reset)
        self._request_id = headers.get('X-Request-Id', self._request_id)
        return response

    def get(self, url, headers=None, params=None, data=None, append_base=True,
            stream=False):

        return self._request(
            'GET', url=url, headers=headers, params=params, data=data,
            append_base=append_base, stream=stream
        )

    def post(self, url, headers=None, params=None, data=None,
             append_base=True):
        return self._request('POST', url=url, headers=headers, params=params,
                             data=data, append_base=append_base)

    def put(self, url, headers=None, params=None, data=None, append_base=True):
        return self._request('PUT', url=url, headers=headers, params=params,
                             data=data, append_base=append_base)

    def patch(self, url, headers=None, params=None, data=None,
              append_base=True):
        return self._request('PATCH', url=url, headers=headers, params=params,
                             data=data, append_base=append_base)

    def delete(self, url, headers=None, params=None, append_base=True):
        return self._request('DELETE', url=url, headers=headers, params=params,
                             data={}, append_base=append_base)

    def __repr__(self):
        return '<API(%s) - "%s">' % (self.url, self.token)

    __str__ = __repr__
