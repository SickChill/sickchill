<%!
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
%>
<%def name="renderQualityPill(quality, overrideClass=None)"><%
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

%><span class="${cssClass}">${qualityString}</span></%def>
