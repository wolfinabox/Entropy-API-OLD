import platform
import datetime
def get_os():
    return platform.system()

def fmt_time(delta:datetime.timedelta):
    """
    Create a formatted string (d:h:m:s:ms) from a timedelta.\n
    Zeroed entries are not shown (which is why this is used instead of strftime)\n
    `delta` The timedelta to format
    """
    ms=int(delta.microseconds/1000.00)
    m, s = divmod(delta.seconds, 60)
    h, m = divmod(m, 60)
    d,h=divmod(h,24)
    d+=delta.days
    ms=f'{ms}ms' if ms>0 else ''
    s=f'{s}s:' if s>0 else ''
    m=f'{m}m:' if m>0 else ''
    h=f'{h}h:' if h>0 else ''
    d=f'{d}d:' if d>0 else ''
    return d+h+m+s+ms