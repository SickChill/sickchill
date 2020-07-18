from validate import Validator
from typing import Sequence
import sickbeard


def assure_config(keys: Sequence[str], copy: bool = False) -> None:
    if keys[0] not in sickbeard.CFG2:
        section = sickbeard.CFG2[keys[0]] = {}
        sickbeard.CFG2.validate(Validator(), section=section, copy=copy)

    if len(keys) > 1 and keys[1] not in sickbeard.CFG2[keys[0]]:
        section = sickbeard.CFG2[keys[0]][keys[1]] = {}
        sickbeard.CFG2.validate(Validator(), section=section, copy=copy)

    if len(keys) > 2 and keys[2] not in sickbeard.CFG2[keys[0]][keys[1]]:
        section = sickbeard.CFG2[keys[0]][keys[1]][keys[2]] = {}
        sickbeard.CFG2.validate(Validator(), section=section, copy=copy)

    if len(keys) > 3 and keys[3] not in sickbeard.CFG2[keys[0]][keys[1]][keys[2]]:
        section = sickbeard.CFG2[keys[0]][keys[1]][keys[2]][keys[3]] = {}
        sickbeard.CFG2.validate(Validator(), section=section, copy=copy)

    if len(keys) > 4 and keys[4] not in sickbeard.CFG2[keys[0]][keys[1]][keys[2]][keys[4]]:
        section = sickbeard.CFG2[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]] = {}
        sickbeard.CFG2.validate(Validator(), section=section, copy=copy)
