import pickle
import json
import os
import logging
from datetime import datetime
logger=logging.getLogger('entropy')
from .wolfinaboxutils.system import script_dir
from .utils import rec_get,rec_put,fmt_time

mem_cache={}
#JSON Method
def cache_get(key,default=None,path=os.path.join(script_dir(),'.cache.json'),key_sep='.'):
    """
    Retrieve an item from the cache.\n
    `key` The key path of the item to get\n
    `default` The value to return if key not found. Default `None`
    """
    start_time = datetime.now()
    #check mem cache
    global mem_cache
    try_memcache=rec_get(key,mem_cache,default,key_sep)
    if try_memcache is not None:
        end_time=fmt_time(datetime.now()-start_time)
        logger.debug(f'Cache Hit for "{key}" (MEMORY)'+f'(Took {end_time})' if end_time else '')
        return try_memcache
    #if the cache file does not exist, create it and return default
    if not os.path.exists(path):
        open(path,'w').close()
        return default
    #open the cache
    with open(path,'r') as f:
        cache={}
        try:
            cache=json.load(f)
        except:
            pass
        finally:
            # _mem_cache['key']=cache.get(key,default)
            val= rec_get(key,cache,default,key_sep)
            if val is not None: 
                end_time=fmt_time(datetime.now()-start_time)
                logger.debug(f'Cache Hit for "{key}" (FILE)'+f'(Took {end_time})' if end_time else '')
                rec_put(key,val,mem_cache,key_sep)
            return val

def cache_put(key,value,path=os.path.join(script_dir(),'.cache.json'),key_sep='.'):
    """
    Save an item to the cache.\n
    `key` The key path of the item to save\n
    `value` The value of the item to save
    """
    global mem_cache
    rec_put(key,value,mem_cache,key_sep)
    if not os.path.exists(path):
        open(path,'w').close()
        return
    #open the cache
    cache={}
    with open(path,'r') as f:
        try:
            cache=json.load(f)
        except:
            pass
    rec_put(key,value,cache,key_sep)
    with open(path,'w') as f:
        json.dump(cache,f,indent=4)

