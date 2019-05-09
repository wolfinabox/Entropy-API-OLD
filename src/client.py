#========================================================#
# File:   client.py - Manages all connections to Discord
# Author: wolfinabox
# GitHub: https://github.com/wolfinabox/Entropy-API
#========================================================#
from .cache import *
from .gateway import Gateway
from .httpclient import HTTPClient
import asyncio
import json
from types import SimpleNamespace
import sys
import logging
import coloredlogs
#Set up logging
logger = logging.getLogger('discord')
logger.addHandler(logging.FileHandler('entropy.log'))
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)
coloredlogs.install(level='DEBUG',logger=logger,fmt='%(asctime)s %(message)s')



class LoginError(Exception):
    pass


class DiscordClient(object):
    """
    A Discord client
    """
    urls = SimpleNamespace(
        main_url='https://discordapp.com',
        login_path='/api/v6/auth/login',
        me_path='/api/v6/users/@me',
        gateway_path='/api/v6/gateway',
        user_path='/api/v6/users/{0}',
        channel_path='/api/v6/channels/{0}',
        cdn='cdn.discordapp.com'
    )
    user_agent = 'Entropy (https://github.com/wolfinabox/Entropy-API)'

    def __init__(self, login_info):
        self.token = None
        self.gateway = None
        self.http = HTTPClient()
        self.discord_data = None
        self.cache = None
        self.login_info = login_info
        self.loop = None

    def start(self):
        """
        Start the client
        """
        self.loop = asyncio.get_event_loop()
        # QUESTIONABLE?
        asyncio.ensure_future(self._start())
        self.loop.run_forever()

    async def _start(self):
        # Try to login
        token = cache_get('token')
        if token is None:
            token, status = await self.http.request('POST', self.urls.main_url, path=self.urls.login_path, data=self.login_info, headers={'Content-Type': 'application/json'})
            # Bad credentials
            if status == 400:
                raise LoginError("Username or Password is incorrect")
            token = token['token']
            cache_put('token', token)
        self.token = token

        # Test me
        me = await self.get_me()

        if me is not None:
            print(
                f'Successfully logged in as "{me["username"]}#{me["discriminator"]}"!')

        # Start Gateway
        gateway_url = cache_get('gateway_url')
        if gateway_url is None:
            gateway_url, status = await self.http.request('GET', self.urls.main_url, path=self.urls.gateway_path)
            gateway_url = gateway_url['url']
            cache_put('gateway_url', gateway_url)
        self.gateway = Gateway(self.token, gateway_url, self.loop)
        # QUESTIONABLE?
        await self.gateway.setup()

    async def get_me(self):
        """
        Get the current logged in user from Discord.\n
        (Probably a temp function)
        """
        resp, stat = await self.http.request('GET', self.urls.main_url, path=self.urls.me_path, headers={'Authorization': self.token})
        if stat == 200:
            return resp
        return None
