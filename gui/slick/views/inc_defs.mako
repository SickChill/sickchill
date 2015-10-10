<%!
    import cgi
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
%>
<%def name="renderQualityPill(quality, showTitle=False, overrideClass=None)"><%
    # Build a string of quality names to use as title attribute
    if showTitle:
        iQuality, pQuality = Quality.splitQuality(quality)
        title = 'Initial Quality:\n'
        if iQuality:
            for curQual in iQuality:
                title += "  " + Quality.qualityStrings[curQual] + "\n"
        else:
            title += "  None\n"
        title += "\nPreferred Quality:\n"
        if pQuality:
            for curQual in pQuality:
                title += "  " + Quality.qualityStrings[curQual] + "\n"
        else:
            title += "  None\n"
        title = ' title="' + cgi.escape(title.rstrip(), True) + '"'
    else:
        title = ""

    iQuality = quality & 0xFFFF
    pQuality = quality >> 16

    # If initial and preferred qualities are the same, show pill as initial quality
    if iQuality == pQuality:
        quality = iQuality

    if quality in qualityPresets:
        cssClass = qualityPresetStrings[quality]
        qualityString = qualityPresetStrings[quality]
    elif quality in Quality.combinedQualityStrings:
        cssClass = Quality.cssClassStrings[quality]
        qualityString = Quality.combinedQualityStrings[quality]
    elif quality in Quality.qualityStrings:
        cssClass = Quality.cssClassStrings[quality]
        qualityString = Quality.qualityStrings[quality]
    else:
        cssClass = "Custom"
        qualityString = "Custom"

    if overrideClass == None:
        cssClass = "quality " + cssClass
    else:
        cssClass = overrideClass

%><span${title} class="${cssClass}">${qualityString}</span></%def>
