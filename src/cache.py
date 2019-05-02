import pickle
import os
from .wolfinaboxutils.system import script_dir

#ALL TEMPORARY, PERFORMANCE WOULD BE BAD, I KNOW


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
