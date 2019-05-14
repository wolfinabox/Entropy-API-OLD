import platform
import datetime


def get_os():
    return platform.system()


def fmt_time(delta: datetime.timedelta):
    """
    Create a formatted string (d:h:m:s:ms) from a timedelta.\n
    Zeroed entries are not shown (which is why this is used instead of strftime)\n
    `delta` The timedelta to format
    """
    ms = int(delta.microseconds/1000.00)
    m, s = divmod(delta.seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    d += delta.days
    ms = f'{ms}ms' if ms > 0 else ''
    s = f'{s}s:' if s > 0 else ''
    m = f'{m}m:' if m > 0 else ''
    h = f'{h}h:' if h > 0 else ''
    d = f'{d}d:' if d > 0 else ''
    return d+h+m+s+ms


def rec_get(key, d: dict, default=None, separator='.'):
    """
    Recursively traverse a dict of dicts and retrieve an item, given a path.\n
    EG: key='n1.2', d={'n1':{'1':'one','2':'two'}}, separator='.' returns 'two'\n
    !ONLY WORKS WITH STRING-TYPE KEYS!\n
    `key` The "path" of keys to follow in the dict\n
    `d` The dict to search\n
    `default` The value to return if key not found (default None)\n
    `separator` The separator to use in `key` (default '.')
    Returns the found value, or `default` if not found
    """
    path = key.split(separator)
    # If the current path part is in the dict
    if path[0] in d:
        val = d[path[0]]
        # If we still need to recurse
        if type(val) == dict and len(path) > 1:
            return rec_get(separator.join(path[1:]), val, default, separator)
        # If there is still path to traverse but no more dicts
        # (EG: path too long)
        elif len(path) > 1:
            return default
        # We found the final value
        else:
            return val
    # Current path part not in the dict
    else:
        return default


def rec_put(key, val, d: dict, separator='.'):
    """
    Recursively traverse a dict of dicts and place an item at the given path (if possible).\n
    See `rec_get()` for usage'\n
    !ONLY WORKS WITH STRING-TYPE KEYS!\n
    `key` The "path" of keys to follow in the dict\n
    `val` The value to place\n
    `d` The dict to search\n
    `separator` The separator to use in `key` (default '.')
    """
    path = key.split(separator)
    # If the current path part is in the dict
    if path[0] in d:
        got_val = d[path[0]]
        # if we still need to recurse
        if type(got_val) == dict and len(path) > 1:
            return rec_put(separator.join(path[1:]), val, got_val, separator)
        # can't put
        elif len(path) > 1:
            return None
        # put
        elif len(path) == 1:
            d[path[0]] = val
            return val
    # Current path part not in the dict
    else:
        #Create the dict and try again
        d[key]={}
        return rec_put(key,val,d,separator)
