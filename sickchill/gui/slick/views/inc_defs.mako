<%!
    from sickchill.oldbeard.common import Quality, qualityPresets, qualityPresetStrings, statusStrings, cssStatusStrings
%>
<%def name="renderQualityPill(quality, showTitle=False, overrideClass=None)">
    <%
        quality=int(quality)
        # Build a string of quality names to use as title attribute
        if showTitle:
            allowed_qualities, preferred_qualities = Quality.splitQuality(quality)
            title = _('Allowed Quality:') + '\n'
            for curQual in allowed_qualities or [None]:
                title += "  " + Quality.qualityStrings[curQual] + "\n"

            title += "\n" + _('Preferred Quality:') + "\n"
            for curQual in preferred_qualities or [None]:
                title += "  " + Quality.qualityStrings[curQual] + "\n"
        else:
            title = ""

        sum_allowed_qualities = quality & 0xFFFF
        sum_preferred_qualities = quality >> 16
        set_hdtv = {Quality.HDTV, Quality.RAWHDTV, Quality.FULLHDTV}
        set_webdl = {Quality.HDWEBDL, Quality.FULLHDWEBDL, Quality.UHD_4K_WEBDL, Quality.UHD_8K_WEBDL}
        set_bluray = {Quality.HDBLURAY, Quality.FULLHDBLURAY, Quality.UHD_4K_BLURAY, Quality.UHD_8K_BLURAY}
        set_1080p = {Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY}
        set_720p = {Quality.HDTV, Quality.RAWHDTV, Quality.HDWEBDL, Quality.HDBLURAY}
        set_uhd_4k = {Quality.UHD_4K_TV, Quality.UHD_4K_BLURAY, Quality.UHD_4K_WEBDL}
        set_uhd_8k = {Quality.UHD_8K_TV, Quality.UHD_8K_BLURAY, Quality.UHD_8K_WEBDL}

        # If allowed and preferred qualities are the same, show pill as allowed quality
        if sum_allowed_qualities == sum_preferred_qualities:
            quality = sum_allowed_qualities

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
        elif set(allowed_qualities).issubset(set_hdtv)and set(preferred_qualities).issubset(set_hdtv):
            cssClass = Quality.cssClassStrings[Quality.ANYHDTV]
            qualityString = 'HDTV'
        # Check if all sources are WEB-DL
        elif set(allowed_qualities).issubset(set_webdl)and set(preferred_qualities).issubset(set_webdl):
            cssClass = Quality.cssClassStrings[Quality.ANYWEBDL]
            qualityString = 'WEB-DL'
        # Check if all sources are BLURAY
        elif set(allowed_qualities).issubset(set_bluray)and set(preferred_qualities).issubset(set_bluray):
            cssClass = Quality.cssClassStrings[Quality.ANYBLURAY]
            qualityString = 'BLURAY'
        # Check if all resolutions are 1080p
        elif set(allowed_qualities).issubset(set_1080p)and set(preferred_qualities).issubset(set_1080p):
            cssClass = Quality.cssClassStrings[Quality.FULLHDBLURAY]
            qualityString = '1080p'
        # Check if all resolutions are 720p
        elif set(allowed_qualities).issubset(set_720p)and set(preferred_qualities).issubset(set_720p):
            cssClass = Quality.cssClassStrings[Quality.HDBLURAY]
            qualityString = '720p'
        # Check if all resolutions are 4K UHD
        elif set(allowed_qualities).issubset(set_uhd_4k)and set(preferred_qualities).issubset(set_uhd_4k):
            cssClass = Quality.cssClassStrings[Quality.HDBLURAY]
            qualityString = '4K-UHD'
        # Check if all resolutions are 8K UHD
        elif set(allowed_qualities).issubset(set_uhd_8k)and set(preferred_qualities).issubset(set_uhd_8k):
            cssClass = Quality.cssClassStrings[Quality.HDBLURAY]
            qualityString = '8K-UHD'
        else:
            cssClass = "Custom"
            qualityString = "Custom"

        cssClass = overrideClass or "quality " + cssClass
    %>
    <span title="${title | h}" data-quality="${quality}" class="${cssClass}">${qualityString}</span>
</%def>


<%def name="renderStatusPill(status)">
    <%
        cssClass = cssStatusStrings.get(status, 'archived')
        statusString = statusStrings[status]
    %>
    <span class="status pill-${cssClass}">${statusString}</span>
</%def>
