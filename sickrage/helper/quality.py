from sickbeard.common import Quality, qualityPresetStrings


def get_quality_string(q):
    if q in qualityPresetStrings:
        return qualityPresetStrings[q]

    if q in Quality.qualityStrings:
        return Quality.qualityStrings[q]

    return 'Custom'
