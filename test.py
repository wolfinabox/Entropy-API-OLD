import json
from src.client import DiscordClient
try:
    client = DiscordClient(login_info=json.load(open('creds.json')))
    client.start()
finally:
    client.loop.run_until_complete(client.http.close())