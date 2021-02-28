from sqlalchemy.orm import mapperlib


def find_table_mapper(table):
    mappers = [
        mapper for mapper in mapperlib._mapper_registry
        if table in mapper.tables
    ]
    if len(mappers) > 1:
        raise ValueError(
            "Multiple mappers found for table '%s'." % table.name
        )
    elif not mappers:
        raise ValueError(
            "Could not get mapper for table '%s'." % table.name
        )
    else:
        return mappers[0]


def reverse_key(info, value):
    return list(info.keys())[list(info.values()).index(value)]
