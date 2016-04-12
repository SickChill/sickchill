<%!
    import sickbeard
    from sickbeard.common import Quality, quality_presets, quality_presetStrings
%>

<%
if show is not UNDEFINED:
    __quality = int(show.quality)
else:
    __quality = int(sickbeard.QUALITY_DEFAULT)

allowed_qualities, preferred_qualities = Quality.splitQuality(__quality)
overall_quality = Quality.combineQualities(allowed_qualities, preferred_qualities)
selected = None
%>

<select id="quality_preset" name="quality_preset" class="form-control form-control-inline input-sm">
    <option value="0">Custom</option>
    % for cur_preset in quality_presets:
        <option value="${cur_preset}" ${('', 'selected="selected"')[cur_preset == overall_quality]} ${('', 'style="padding-left: 15px;"')[quality_presetStrings[cur_preset].endswith("0p")]}>${quality_presetStrings[cur_preset]}</option>
    % endfor
</select>

<div id="customQualityWrapper">
    <div id="customQuality" style="padding-left: 0px;">
        ${_('<p><b><u>Preferred</u></b> qualities will replace those in <b><u>allowed</u></b>, even if they are lower.</p>')}

        <div style="padding-right: 40px; text-align: left; float: left;">
            <h5>${_('Allowed')}</h5>
            <% allowedQualityList = filter(lambda x: x > Quality.NONE, Quality.qualityStrings) %>
            <select id="allowed_qualities" name="allowed_qualities" multiple="multiple" size="${len(allowedQualityList)}" class="form-control form-control-inline input-sm">
            % for cur_quality in sorted(allowedQualityList):
                <option value="${cur_quality}" ${('', 'selected="selected"')[cur_quality in allowed_qualities]}>${Quality.qualityStrings[cur_quality]}</option>
            % endfor
            </select>
        </div>

        <div style="text-align: left; float: left;">
            <h5>${_('Preferred')}</h5>
            <% preferredQualityList = filter(lambda x: x >= Quality.SDTV and x < Quality.UNKNOWN, Quality.qualityStrings) %>
            <select id="preferred_qualities" name="preferred_qualities" multiple="multiple" size="${len(preferredQualityList)}" class="form-control form-control-inline input-sm">
            % for cur_quality in sorted(preferredQualityList):
                <option value="${cur_quality}" ${('', 'selected="selected"')[cur_quality in preferred_qualities]}>${Quality.qualityStrings[cur_quality]}</option>
            % endfor
            </select>
        </div>
    </div>
</div>
