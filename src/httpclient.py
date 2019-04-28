import aiohttp
import json
class HTTPClient(object):
    def __init__(self):
        self.http_session = aiohttp.ClientSession()
    async def close(self):
        await self.http_session.close()
    async def request(self,method: str, url: str, **kwargs):
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
        resp = None
        

        #Modify headers
        headers=kwargs.get('headers',{})
        if 'data' in kwargs:
            headers['Content-Length']=str(len(json.dumps(kwargs['data'])))
        if method.upper() == 'POST':
            resp = await self.http_session.post(url+kwargs.get('path',''), json=kwargs.get('data',None),headers=headers)
        else:
            resp = await self.http_session.get(url+kwargs.get('path',''),json=kwargs.get('data',None),headers=headers)
        result=await resp.text(encoding=kwargs.get('encoding','utf-8'))
        return (json.loads(result) if kwargs.get('json',True) else result),resp.status