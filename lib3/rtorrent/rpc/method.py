import re

METHOD_TYPE_RETRIEVER = 0
METHOD_TYPE_MODIFIER = 1
METHOD_TYPE_RE = re.compile("\.?set_")
METHOD_VAR_NAME_RE = re.compile("([ptdf]\.|system\.|get\_|is\_|set\_)+([^=]*)")

int_to_bool = lambda x: x in [1, "1"]
check_success = lambda x: x == 0

def valmap(from_list, to_list, arg_index):
    def func(*args):
        args = list(args)
        args[arg_index] = to_list[from_list.index(args[arg_index])]
        return tuple(args)

    return func


class RPCMethod(object):
    def __init__(self, method_names, *args, **kwargs):
        if isinstance(method_names, str):
            method_names = (method_names,)

        self.method_names = tuple(method_names)
        self.method_type = kwargs.get("method_type",
                                      self._identify_method_type())
        self.var_name = kwargs.get("var_name", self._identify_var_name())
        self.pre_processors = kwargs.get("pre_processors", [])
        self.post_processors = kwargs.get("post_processors", [])

        if kwargs.get("boolean", False):
            self.post_processors.append(int_to_bool)


        self.pre_processors = tuple(self.pre_processors)
        self.post_processors = tuple(self.post_processors)

    def get_key(self):
        return self.key

    def get_method_names(self):
        return self.method_names

    def get_var_name(self):
        return self.var_name

    def get_pre_processors(self):
        return tuple(self.pre_processors)

    def get_post_processors(self):
        return tuple(self.post_processors)

    def get_available_method_name(self, available_methods):
        matches = set(self.get_method_names()).intersection(available_methods)
        return matches.pop() if len(matches) > 0 else None

    def is_available(self, available_methods) -> bool:
        return self.get_available_method_name(available_methods) is not None

    def is_retriever(self) -> bool:
        return self._identify_method_type() == METHOD_TYPE_RETRIEVER

    def _identify_method_type(self):
        match = METHOD_TYPE_RE.search(self.method_names[0])
        return METHOD_TYPE_MODIFIER if match else METHOD_TYPE_RETRIEVER

    def _identify_var_name(self):
        match = re.match(METHOD_VAR_NAME_RE, self.method_names[0])
        if match is None:
            raise Exception("Could not id var_name for method: {0}"
                            .format(self.method_names))

        return match.groups(-1)
