<%!
    from sickchill import settings
    from sickchill.oldbeard.common import Quality, qualityPresets, qualityPresetStrings
%>

<%
if show is not UNDEFINED:
    __quality = int(show.quality)
else:
    __quality = int(settings.QUALITY_DEFAULT)

anyQualities, bestQualities = Quality.splitQuality(__quality)
overall_quality = Quality.combineQualities(anyQualities, bestQualities)
selected = None
%>

<div class="row">
    <div class="col-md-12">
        <select id="qualityPreset" name="quality_preset" class="form-control input-sm input100" title="qualityPreset">
            <option value="0">Custom</option>
            % for curPreset in qualityPresets:
                <option value="${curPreset}" ${('', 'selected="selected"')[curPreset == overall_quality]} ${('', 'style="padding-left: 15px;"')[qualityPresetStrings[curPreset].endswith("0p")]}>${qualityPresetStrings[curPreset]}</option>
            % endfor
        </select>
    </div>
</div>
<div class="row">
    <div class="col-md-12">
        <div id="customQualityWrapper">
            <div id="customQuality" style="padding-left: 0;">
                ${_('<p><b><u>Preferred</u></b> qualities will replace those in <b><u>allowed</u></b>, even if they are lower.</p>')}

                <div style="padding-right: 40px; text-align: left; float: left;">
                    <h5>${_('Allowed')}</h5>
                    <% anyQualityList = [x for x in Quality.qualityStrings if x > Quality.NONE] %>
                    <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}" class="form-control form-control-inline input-sm" title="anyQualities">
                        % for curQuality in sorted(anyQualityList):
                            <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in anyQualities]}>${Quality.qualityStrings[curQuality]}</option>
                        % endfor
                    </select>
                </div>

                <div style="text-align: left; float: left;">
                    <h5>${_('Preferred')}</h5>
                    <% bestQualityList = [x for x in Quality.qualityStrings if Quality.SDTV <= x < Quality.UNKNOWN] %>
                    <select id="bestQualities" name="bestQualities" multiple="multiple" size="${len(bestQualityList)}" class="form-control form-control-inline input-sm" title="bestQualities">
                        % for curQuality in sorted(bestQualityList):
                            <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in bestQualities]}>${Quality.qualityStrings[curQuality]}</option>
                        % endfor
                    </select>
                </div>
            </div>
        </div>
    </div>
</div>
