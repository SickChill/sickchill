import datetime

def valmap(from_list, to_list, index=0):
    assert len(from_list) == len(to_list)
    def inner(*args):
        args = list(args)
        to_list_i = from_list.index(args[index])
        args[index] = to_list[to_list_i]
        return args

    return inner

def choose(arg):
    def inner(*args):
        if isinstance(arg, int):
            return args[arg]
        elif isinstance(arg, (list, range)):
            return list(map(lambda i: args[i], arg))
        else:
            raise AttributeError('Unhandled type {0}'.format(type(arg)))

    return inner

def int_to_bool(arg):
    return arg in [1, '1']

def bool_to_int(arg):
    return 1 if arg else 0

def check_success(arg):
    return arg == 0

def us_to_datetime(arg):
    return to_datetime(arg)

def s_to_datetime(arg):
    # Return None if RTorrent returns a timestamp of zero
    if arg <= 0:
        return None
    
    # RTorrent timestamps are converted to UTC
    # utcfromtimestamp will return a generic datetime object
    # without a timezone associated with it
    return datetime.datetime.utcfromtimestamp(arg) \
        .replace(tzinfo=datetime.timezone.utc)

def to_datetime(arg):
    # Return None if RTorrent returns a timestamp of zero
    if arg <= 0:
        return None

    # RTorrent timestamps are in microseconds, we need them it in seconds
    arg /= 1.0E6

    # RTorrent timestamps are converted to UTC
    # utcfromtimestamp will return a generic datetime object
    # without a timezone associated with it
    return datetime.datetime.utcfromtimestamp(arg) \
        .replace(tzinfo=datetime.timezone.utc)
