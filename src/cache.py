import pickle
import json
import os
from .wolfinaboxutils.system import script_dir
from .utils import rec_get,rec_put
#ALL TEMPORARY, PERFORMANCE WOULD BE BAD, I KNOW
#Pickle Method
'''
def cache_get(key,default=None,path=os.path.join(script_dir(),'.cache')):
    """
    Retrieve an item from the cache file.\n
    `key` The key of the item to get\n
    `default` The value to return if key not found. Default `None`
    """   
    #if the cache file does not exist, create it and return default
    if not os.path.exists(path):
        open(path,'wb').close()
        return default
    #open the cache
    with open(path,'rb') as f:
        cache={}
        try:
            cache=pickle.load(f)
        except:
            pass
        finally:
            # _mem_cache['key']=cache.get(key,default)
            return cache.get(key,default)

def cache_put(key,value,path=os.path.join(script_dir(),'.cache')):
    """
    Save an item from the cache file.\n
    `key` The key of the item to save\n
    `value` The value of the item to save
    """
    if not os.path.exists(path):
        open(path,'wb').close()
        return
    #open the cache
    cache={}
    with open(path,'rb') as f:
        try:
            cache=pickle.load(f)
        except:
            pass
    cache[key]=value
    with open(path,'wb') as f:
        pickle.dump(cache,f)
'''

mem_cache={}
#JSON Method
def cache_get(key,default=None,path=os.path.join(script_dir(),'.cache.json'),key_sep='.'):
    """
    Retrieve an item from the cache.\n
    `key` The key path of the item to get\n
    `default` The value to return if key not found. Default `None`
    """
    #check mem cache
    global mem_cache
    try_memcache=rec_get(key,mem_cache,default,key_sep)
    if try_memcache is not None:
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
            if val is not None: rec_put(key,val,mem_cache,key_sep)
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

