import collections

from rtorrent.rpc.call import RPCCall

class RPCResult(object):
    def __init__(self, rpc_calls: [RPCCall], results):
        self._rpc_calls_results_map = collections.OrderedDict()
        for call, result in zip(rpc_calls, results):
            self._rpc_calls_results_map[call] = result

    def __getitem__(self, item):
        if isinstance(item, RPCCall):
            return self._rpc_calls_results_map[item]
        elif isinstance(item, int):
            key = list(self._rpc_calls_results_map.keys())[item]
            return self._rpc_calls_results_map[key]
        else:
            raise AttributeError('Received unsupported item')

    def __iter__(self):
        for key in self._rpc_calls_results_map:
            yield (key, self._rpc_calls_results_map[key])

    def __len__(self):
        return len(self._rpc_calls_results_map)
