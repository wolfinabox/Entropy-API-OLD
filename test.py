import json
from src.client import DiscordClient
try:
    #TEMPORARY, SO I DON'T COMMIT MY LOGIN :)
    client = DiscordClient(login_info=json.load(open('creds.json')))
    client.start()
finally:
    client.loop.run_until_complete(client.http.close())