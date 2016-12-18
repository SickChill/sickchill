from .taskrouter_config import TaskRouterConfig
import json


class WorkflowConfig:

    """
    WorkflowConfig represents the whole workflow config json which contains
    filters and default_filter.
    """

    def __init__(self, workflow_rules, default_target):
        # filters and default_filters
        self.task_routing = TaskRouterConfig(workflow_rules, default_target)

    def to_json(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=4)

    @staticmethod
    def json2obj(data):
        m = json.loads(data)
        return WorkflowConfig(m['task_routing']['filters'],
                              m['task_routing']['default_filter'])
