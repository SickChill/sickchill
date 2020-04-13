from migrate.changeset import SQLA_10


def fk_column_names(constraint):
    if SQLA_10:
        return [
            constraint.columns[key].name for key in constraint.column_keys]
    else:
        return [
            element.parent.name for element in constraint.elements]
