<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import adba
    from sickbeard import common
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import statusStrings
    from sickbeard import exceptions
    from sickbeard import scene_exceptions
%>
<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/qualityChooser.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/lib/bootstrap-formhelpers.min-2.3.0.js?${sbPID}"></script>
<script type="text/javascript" charset="utf-8">
    var all_exceptions = new Array;

    $('#location').fileBrowser({ title: 'Select Show Location' });

    $('#submit').click(function(){
        all_exceptions = []

        $("#exceptions_list option").each  ( function() {
            all_exceptions.push( $(this).val() );
        });

        $("#exceptions_list").val(all_exceptions);

        % if show.is_anime:
            generate_bwlist()
        % endif
        });
    $('#addSceneName').click(function() {
        var scene_ex = $('#SceneName').val()
        var option = $("<option>")
        all_exceptions = []

        $("#exceptions_list option").each  ( function() {
           all_exceptions.push( $(this).val() )
        });

        $('#SceneName').val('')

        if ($.inArray(scene_ex, all_exceptions) > -1 || (scene_ex == ''))
            return

        $("#SceneException").show()

        option.attr("value",scene_ex)
        option.html(scene_ex)
        return option.appendTo('#exceptions_list');
    });

    $('#removeSceneName').click(function() {
        $('#exceptions_list option:selected').remove();

        $(this).toggle_SceneException()
    });

   $.fn.toggle_SceneException = function() {
        all_exceptions = []

        $("#exceptions_list option").each  ( function() {
            all_exceptions.push( $(this).val() );
        });

        if (all_exceptions == '')
            $("#SceneException").hide();
        else
            $("#SceneException").show();
    }

    $(this).toggle_SceneException();
</script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="editShow">
<form action="editShow" method="post">
<input type="hidden" name="show" value="${show.indexerid}" />
<b>Location:</b></br>
<input type="text" name="location" id="location" value="${show._location}" class="form-control form-control-inline input-sm input350" /><br />
<br />

<b>Scene Exception:</b><br />
<input type="text" id="SceneName" class="form-control form-control-inline input-sm input200">
<input class="btn btn-inline" type="button" value="Add" id="addSceneName"><br />
This will <b>affect the episode show search</b> on nzb and torrent provider.<br />
        This list overrides the original name, it doesn't append to it.<br />

<div id="SceneException" >
    <div class="pull-left" style="text-align:center;">
        <h4>Exceptions List</h4>
        <select id="exceptions_list" name="exceptions_list" multiple="multiple" style="min-width:10em;" >
                % for cur_exception in show.exceptions:
                    <option value="${cur_exception}">${cur_exception}</option>
                % endfor
        </select>
        <div>
            <input id="removeSceneName" value="Remove" class="btn float-left" type="button" style="margin-top: 10px;"/>
        </div>
        <br />
    </div>
</div>
<div class="clearfix"></div>
<br />

<b>Quality:</b><br />
<%
    qualities = common.Quality.splitQuality(int(show.quality))
    anyQualities = qualities[0]
    bestQualities = qualities[1]
%>
<%include file="/inc_qualityChooser.mako"/>
<br />

<b>Default Episode Status:</b><br />
(this will set the status for future episodes)<br />
<select name="defaultEpStatus" id="defaultEpStatusSelect" class="form-control form-control-inline input-sm">
    % for curStatus in [WANTED, SKIPPED, ARCHIVED, IGNORED]:
    <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == show.default_ep_status]}>${statusStrings[curStatus]}</option>
    % endfor
</select><br />
<br />

<b>Info Language:</b><br />
(this will only affect the language of the retrieved metadata file contents and episode filenames)<br />
<select name="indexerLang" id="indexerLangSelect" class="form-control form-control-inline input-sm bfh-languages" data-language="${show.lang}" data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}"></select><br />
<br />
<b>Flatten files (no folders): </b> <input type="checkbox" name="flatten_folders" ${('', 'checked="checked"')[show.flatten_folders == 1 and not sickbeard.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(sickbeard.NAMING_FORCE_FOLDERS)]}/><br />
(Disabled: episodes folder-grouped by season. Enabled: no season folders)<br/>
<br />

<b>Paused: </b> <input type="checkbox" name="paused" ${('', 'checked="checked"')[show.paused == 1]} /><br />
(check this if you wish to pause this show. Will not download anything until unpause)<br/>
<br />

<b>Subtitles: </b> <input type="checkbox" name="subtitles" ${('', 'checked="checked"')[show.subtitles == 1 and sickbeard.USE_SUBTITLES == True]} ${('disabled="disabled"', '')[bool(sickbeard.USE_SUBTITLES)]}/><br />
(check this if you wish to search for subtitles in this show)<br/>
<br />

<b>Scene Numbering: </b>
<input type="checkbox" name="scene" ${('', 'checked="checked"')[show.scene == 1]} /><br/>
(check this if you wish to search by scene numbering, uncheck to search by indexer numbering)<br/>
<br/>

<b>Air by date: </b>
<input type="checkbox" name="air_by_date" ${('', 'checked="checked"')[show.air_by_date == 1]} /><br />
(check this if the show is released as Show.03.02.2010 rather than Show.S02E03. <span style="color:red">In case air date conflict between regular and special episodes, the later will be ignored.</span>)<br />
<br />

<b>Sports: </b>
<input type="checkbox" name="sports" ${('', 'checked="checked"')[show.sports == 1]}/><br />
(check this if the show is a sporting or MMA event and released as Show.03.02.2010 rather than Show.S02E03. <span style="color:red">In case air date conflict between regular and special episodes, the later will be ignored.</span>)<br />
<br />

<b>Anime: </b>
<input type="checkbox" name="anime" ${('', 'checked="checked"')[show.is_anime == 1]}><br />
(check this if the show is released as Show.265 rather than Show.S02E03, this show is an anime)<br />
<br />

<b>DVD Order: </b>
<input type="checkbox" name="dvdorder" ${('', 'checked="checked"')[show.dvdorder == 1]} /><br/>
(check this if you wish to use the DVD order instead of the Airing order. A "Force Full Update" is necessary, and if you have existing episodes you need to move them)
<br/><br/>

% if anyQualities + bestQualities:
<b>Archive on first match:</b>
<input type="checkbox" name="archive_firstmatch" ${('', 'checked="checked"')[show.archive_firstmatch == 1]} /><br>
(check this to have the episode archived after the first best match is found from your archive quality list)</br>
<br />
% endif

<b>Ignored Words:</b></br>
<input type="text" name="rls_ignore_words" id="rls_ignore_words" value="${show.rls_ignore_words}" class="form-control form-control-inline input-sm input350" /><br />
Results with one or more word from this list will be ignored<br />
Separate words with a comma, e.g. "word1,word2,word3"<br />
<br />

<b>Required Words:</b></br>
<input type="text" name="rls_require_words" id="rls_require_words" value="${show.rls_require_words}" class="form-control form-control-inline input-sm input350" /><br />
Results with no word from this list will be ignored<br />
Separate words with a comma, e.g. "word1,word2,word3"<br />
<br />

% if show.is_anime:
    <%include file="/inc_blackwhitelist.mako"/>
    <script type="text/javascript" src="${sbRoot}/js/blackwhite.js?${sbPID}"></script>
% endif

<input type="submit" id="submit" value="Submit" class="btn btn-primary" />
</form>
</div>
</%block>
