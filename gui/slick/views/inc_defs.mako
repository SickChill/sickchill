<%!
    import cgi
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
%>
<%def name="renderQualityPill(quality, showTitle=False, overrideClass=None)"><%
    # Build a string of quality names to use as title attribute
    if showTitle:
        iquality, pquality = Quality.splitQuality(quality)
        title = 'Initial Quality:\n'
        if iquality:
            for curQual in iquality:
                title += "  " + Quality.qualityStrings[curQual] + "\n"
        else:
            title += "  None\n"
        title += "\nPreferred Quality:\n"
        if pquality:
            for curQual in pquality:
                title += "  " + Quality.qualityStrings[curQual] + "\n"
        else:
            title += "  None\n"
        title = ' title="' + cgi.escape(title.rstrip(), True) + '"'
    else:
        title = ""

    sum_iquality = quality & 0xFFFF
    sum_pquality = quality >> 16
    set_hdtv = {Quality.HDTV, Quality.RAWHDTV, Quality.FULLHDTV}
    set_webdl = {Quality.HDWEBDL, Quality.FULLHDWEBDL, Quality.UHD_4K_WEBDL, Quality.UHD_8K_WEBDL}
    set_bluray = {Quality.HDBLURAY, Quality.FULLHDBLURAY, Quality.UHD_4K_BLURAY, Quality.UHD_8K_BLURAY}
    set_1080p = {Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY}
    set_720p = {Quality.HDTV, Quality.RAWHDTV, Quality.HDWEBDL, Quality.HDBLURAY}
    set_uhd_4k = {Quality.UHD_4K_TV, Quality.UHD_4K_BLURAY, Quality.UHD_4K_WEBDL}
    set_uhd_8k = {Quality.UHD_8K_TV, Quality.UHD_8K_BLURAY, Quality.UHD_8K_WEBDL}

    # If initial and preferred qualities are the same, show pill as initial quality
    if sum_iquality == sum_pquality:
        quality = sum_iquality

    if quality in qualityPresets:
        cssClass = qualityPresetStrings[quality]
        qualityString = qualityPresetStrings[quality]
    elif quality in Quality.combinedQualityStrings:
        cssClass = Quality.cssClassStrings[quality]
        qualityString = Quality.combinedQualityStrings[quality]
    elif quality in Quality.qualityStrings:
        cssClass = Quality.cssClassStrings[quality]
        qualityString = Quality.qualityStrings[quality]
    # Check if all sources are HDTV
    elif set(iquality).issubset(set_hdtv)and set(pquality).issubset(set_hdtv):
        cssClass = Quality.cssClassStrings[Quality.ANYHDTV]
        qualityString = 'HDTV'
    # Check if all sources are WEB-DL
    elif set(iquality).issubset(set_webdl)and set(pquality).issubset(set_webdl):
        cssClass = Quality.cssClassStrings[Quality.ANYWEBDL]
        qualityString = 'WEB-DL'
    # Check if all sources are BLURAY
    elif set(iquality).issubset(set_bluray)and set(pquality).issubset(set_bluray):
        cssClass = Quality.cssClassStrings[Quality.ANYBLURAY]
        qualityString = 'BLURAY'
    # Check if all resolutions are 1080p
    elif set(iquality).issubset(set_1080p)and set(pquality).issubset(set_1080p):
        cssClass = Quality.cssClassStrings[Quality.FULLHDBLURAY]
        qualityString = '1080p'
    # Check if all resolutions are 720p
    elif set(iquality).issubset(set_720p)and set(pquality).issubset(set_720p):
        cssClass = Quality.cssClassStrings[Quality.HDBLURAY]
        qualityString = '720p'
    # Check if all resolutions are 4K UHD
    elif set(iquality).issubset(set_uhd_4k)and set(pquality).issubset(set_uhd_4k):
        cssClass = Quality.cssClassStrings[Quality.HDBLURAY]
        qualityString = '4K-UHD'
    # Check if all resolutions are 8K UHD
    elif set(iquality).issubset(set_uhd_8k)and set(pquality).issubset(set_uhd_8k):
        cssClass = Quality.cssClassStrings[Quality.HDBLURAY]
        qualityString = '8K-UHD'
    else:
        cssClass = "Custom"
        qualityString = "Custom"

    if overrideClass is None:
        cssClass = "quality " + cssClass
    else:
        cssClass = overrideClass

%><span${title} class="${cssClass}">${qualityString}</span></%def>
