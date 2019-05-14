#========================================================#
# File:   httpclient.py - Handles http requests
# Author: wolfinabox
# GitHub: https://github.com/wolfinabox/Entropy-API
#========================================================#
from datetime import timedelta, datetime
from .utils import fmt_time
import aiohttp
import json
import logging
logger = logging.getLogger('discord')


class HTTPClient(object):
    def __init__(self,loop):
        self.http_session = aiohttp.ClientSession()
        self.loop=loop

    async def close(self):
        """
        Close the HTTP session.
        """
        await self.http_session.close()

    async def request(self, method: str, url: str, **kwargs):
        """
        Make an HTTPS POST/GET request.\n
        `method` The request method to use (POST/GET)\n
        `url` The URL to request to\n
        kwargs:\n
        `path` The path to request to (appended to `url`)\n
        `data` The data (dict) to send. Default None\n
        `headers` The headers object. Default None\n
        `encoding` The encoding to use. Default `utf-8`\n
        `json` Whether to parse the results into JSON. Default `True`.\n
        `Returns` None if request failed, otherwise the gathered data in a string or JSON object.
        """
        # Reopen HTTP session if it's closed
        if self.http_session.closed:
            self.http_session = aiohttp.ClientSession(loop=loop)

        start_time = datetime.now()
        resp = None
        # Modify headers
        headers = kwargs.get('headers', {})
        if 'data' in kwargs:
            headers['Content-Length'] = str(len(json.dumps(kwargs['data'])))

        # Make request
        if method.upper() == 'POST':
            resp = await self.http_session.post(url+kwargs.get('path', ''), json=kwargs.get('data', None), headers=headers)
        elif method.upper() == 'GET':
            resp = await self.http_session.get(url+kwargs.get('path', ''), json=kwargs.get('data', None), headers=headers)
        else:
            raise NotImplementedError(f'HTTP Request type {method}')
        result = await resp.text(encoding=kwargs.get('encoding', 'utf-8'))

        end_time = datetime.now()-start_time
        logger.debug(
            f'HTTP Request to {url+kwargs.get("path","")} finished with status {resp.status}. (Took {fmt_time(end_time)})')
        return (json.loads(result) if kwargs.get('json', True) else result), resp.status
