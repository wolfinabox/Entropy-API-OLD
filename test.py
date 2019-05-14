import json
import time 
import asyncio
import logging
from src.client import DiscordClient

def callback(future:asyncio.futures.Future):
    logger = logging.getLogger('discord')
    res=future.result()
    logger.info(res)

try:
    #TEMPORARY, SO I DON'T COMMIT MY LOGIN :)
    #TO USE, CREATE A 'creds.json' FILE NEXT TO THIS FILE, AND PUT YOUR DISCORD LOGIN DETAILS IN LIKE SUCH:
    #{"email": "your_email_here", "password": "your_password_here"}
    client = DiscordClient(login_info=json.load(open('creds.json')))
    time.sleep(5)
    asyncio.run_coroutine_threadsafe(client.get_me(),client.loop).add_done_callback(callback)
finally:
    pass