from .workflow_ruletarget import WorkflowRuleTarget


class WorkflowRule:

    """
    WorkflowRule represents the top level filter
    which contains a 1 or more targets

    ..attribute::expression

       The expression at the top level filter

    ..attribute::targets

       The list of targets under the filter

    ..attribute::friendlyName

       The name of the filter
    """

    def __init__(self, expression, targets, friendly_name):

        self.expression = expression
        self.targets = targets
        self.friendly_name = friendly_name

    def __repr__(self):
        return str({
            'expression': self.expression,
            'friendly_name': self.friendly_name,
            'targets': self.targets,
        })
