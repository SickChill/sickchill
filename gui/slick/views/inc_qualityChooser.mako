<%!
    import sickbeard
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
%>

<%
if show is not UNDEFINED:
    __quality = int(show.quality)
else:
    __quality = int(sickbeard.QUALITY_DEFAULT)

anyQualities, bestQualities = Quality.splitQuality(__quality)
overall_quality = Quality.combineQualities(anyQualities, bestQualities)
selected = None
%>

<select id="qualityPreset" name="quality_preset" class="form-control form-control-inline input-sm">
    <option value="0">Custom</option>
    % for cur_preset in qualityPresets:
        <option value="${cur_preset}" ${('', 'selected="selected"')[cur_preset == overall_quality]} ${('', 'style="padding-left: 15px;"')[qualityPresetStrings[cur_preset].endswith("0p")]}>${qualityPresetStrings[cur_preset]}</option>
    % endfor
</select>

<div id="customQualityWrapper">
    <div id="customQuality" style="padding-left: 0px;">
        ${_('<p><b><u>Preferred</u></b> qualities will replace those in <b><u>allowed</u></b>, even if they are lower.</p>')}

        <div style="padding-right: 40px; text-align: left; float: left;">
            <h5>${_('Allowed')}</h5>
            <% anyQualityList = filter(lambda x: x > Quality.NONE, Quality.qualityStrings) %>
            <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}" class="form-control form-control-inline input-sm">
            % for cur_quality in sorted(anyQualityList):
                <option value="${cur_quality}" ${('', 'selected="selected"')[cur_quality in anyQualities]}>${Quality.qualityStrings[cur_quality]}</option>
            % endfor
            </select>
        </div>

        <div style="text-align: left; float: left;">
            <h5>${_('Preferred')}</h5>
            <% bestQualityList = filter(lambda x: x >= Quality.SDTV and x < Quality.UNKNOWN, Quality.qualityStrings) %>
            <select id="bestQualities" name="bestQualities" multiple="multiple" size="${len(bestQualityList)}" class="form-control form-control-inline input-sm">
            % for cur_quality in sorted(bestQualityList):
                <option value="${cur_quality}" ${('', 'selected="selected"')[cur_quality in bestQualities]}>${Quality.qualityStrings[cur_quality]}</option>
            % endfor
            </select>
        </div>
    </div>
</div>
