from rtorrent.rpc.method import RPCMethod

class RPCCall(object):
    def __init__(self, rpc_method: RPCMethod, *args):
        self.rpc_method = rpc_method
        self.args = list(args)

    def get_method(self) -> RPCMethod:
        return self.rpc_method

    def get_args(self) -> list:
        return self.args

    def do_pre_processing(self):
        for processor in self.get_method().get_pre_processors():
            self.args = processor(*self.get_args())

    def do_post_processing(self, result):
        for processor in self.get_method().get_post_processors():
            result = processor(result)

        return result