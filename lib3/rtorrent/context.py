class RTContext(object):
    def __init__(self):
        print("here")

    def get_conn(self):
        raise NotImplementedError

    def get_available_rpc_methods(self):
        raise NotImplementedError
