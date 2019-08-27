# coding=utf-8
# __author__ = 'Mio'
import ujson as json_mod
from typing import Awaitable

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse
from tornado.httputil import url_concat, urlencode

http_client = AsyncHTTPClient()


def get(
    url: [str, HTTPRequest],
    params: dict = None,
    raise_error: bool = True,
    **kwargs
) -> Awaitable["HTTPResponse"]:
    if kwargs.get('validate_cert') is None:
        kwargs['validate_cert'] = False

    if not isinstance(url, HTTPRequest):
        request = HTTPRequest(method="GET", url=url_concat(url, params), **kwargs)
    else:
        request = url

    return http_client.fetch(request, raise_error=raise_error)


def post(url, data=None, json=None, raise_error=True, **kwargs):
    if kwargs.get('validate_cert') is None:
        kwargs['validate_cert'] = False

    if not isinstance(url, HTTPRequest):
        if data:
            request = HTTPRequest(method="POST", url=url_concat(url, kwargs.get("params", None)),
                                  body=urlencode(data), **kwargs)
        elif json:
            headers = kwargs.get("headers", {})
            headers['Content-Type'] = "application/json"
            request = HTTPRequest(method="POST", url=url_concat(url, kwargs.get("params", None)),
                                  body=json_mod.dumps(json), **kwargs)
        else:
            request = HTTPRequest(method="POST", url=url_concat(url, kwargs.get("params", None)),
                                  **kwargs)
    else:
        request = url

    return http_client.fetch(request, raise_error=raise_error)


def head(url, params=None, raise_error=True, **kwargs):
    if kwargs.get('validate_cert') is None:
        kwargs['validate_cert'] = False

    if not isinstance(url, HTTPRequest):
        request = HTTPRequest(method="HEAD", url=url_concat(url, params), **kwargs)
    else:
        request = url

    return http_client.fetch(request, raise_error=raise_error)


def parse_body2json(response: HTTPResponse):
    return json_mod.loads(response.body)


class GAsyncHTTPClient(AsyncHTTPClient):
    def get(self, url, params=None, raise_error=True, **kwargs):
        if not isinstance(url, HTTPRequest):
            url = HTTPRequest(url=url_concat(url, params), **kwargs)

        return self.fetch(url, raise_error=raise_error)
