import json


from src.client import DiscordClient
try:
    #TEMPORARY, SO I DON'T COMMIT MY LOGIN :)
    #TO USE, CREATE A 'creds.json' FILE NEXT TO THIS FILE, AND PUT YOUR DISCORD LOGIN DETAILS IN LIKE SUCH:
    #{"email": "your_email_here", "password": "your_password_here"}
    client = DiscordClient(login_info=json.load(open('creds.json')))
    client.start()
finally:
    client.loop.run_until_complete(client.http.close())