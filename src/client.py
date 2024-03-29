#========================================================#
# File:   client.py - Manages all connections to Discord
# Author: wolfinabox
# GitHub: https://github.com/wolfinabox/Entropy-API
#========================================================#
__version__='0.0.1'
if __name__=='__main__':
    print(f'Entropy v{__version__} https://github.com/wolfinabox/Entropy-API')
    quit()

import sys
from .cache import *
from .gateway import Gateway
from .httpclient import HTTPClient
import asyncio
import json
from types import SimpleNamespace
import logging
import coloredlogs

from threading import Thread #TODO: PUT ALL THE ASYNC SHIT IN ITS OWN THREAD, START THE LOOP THERE? IDK MAN

#Set up logging
logger = logging.getLogger('entropy-client')
log_names=['entropy-client','entropy-gateway','entropy-httpclient']
for tmp in log_names:
    tmp=logging.getLogger(tmp)
    tmp.addHandler(logging.FileHandler('entropy.log'))
    tmp.addHandler(logging.StreamHandler(sys.stdout))
    tmp.setLevel(logging.DEBUG)
    coloredlogs.install(level='DEBUG',logger=tmp,fmt='%(asctime)s %(name)s - %(message)s')


class LoginError(Exception):
    """
    Exception thrown when the Discord client was unable to login using the given credentials.
    """
    pass


class DiscordClient(Thread):
    """
    A Discord client. Handles all connections to and from the Discord API.\n
    See documentation here https://discordapp.com/developers/docs/intro
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
        self.login_info = login_info
        Thread.__init__(self)
        self.start()

    def run(self):
        """
        Start the client
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.token:str = None
        self.gateway:Gateway = None
        self.http = HTTPClient(self.loop)
        self.discord_data:dict = None
        self.cache = None
        #TODO WANT TO CATCH EXCEPTIONS HERE, OR IN TEST.PY.
        #NOT WORKING
        try:
            asyncio.ensure_future(self._start(),loop=self.loop)
            self.loop.run_forever()
        except Exception:
            logger.error('Username/Password incorrect!')
            raise

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
        else:
            raise LoginError('Couldn\'t log in')

        # Start Gateway
        gateway_url = cache_get('gateway_url')
        if gateway_url is None:
            gateway_url, status = await self.http.request('GET', self.urls.main_url, path=self.urls.gateway_path)
            gateway_url = gateway_url['url']
            cache_put('gateway_url', gateway_url)
        self.gateway = Gateway(self.token, gateway_url, self.loop)
        await self.gateway.setup()

    #PROBABLY A TEMP FUNCTION
    async def get_me(self):
        """
        Get the current logged in user from Discord.\n
        (Probably a temp function)
        """
        resp, stat = await self.http.request('GET', self.urls.main_url, path=self.urls.me_path, headers={'Authorization': self.token})
        if stat == 200:
            return resp
        return None
