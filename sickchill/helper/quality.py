from sickchill.oldbeard.common import Quality, qualityPresetStrings


def get_quality_string(quality):
    """
    :param quality: The quality to convert into a string
    :return: The string representation of the provided quality
    """

    if quality in qualityPresetStrings:
        return qualityPresetStrings[quality]

    if quality in Quality.qualityStrings:
        return Quality.qualityStrings[quality]

    return "Custom"
