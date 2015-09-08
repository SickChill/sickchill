<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>
<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/formwizard.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/qualityChooser.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/newShow.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/addShowOptions.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/lib/bootstrap-formhelpers.min-2.3.0.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/rootDirs.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/blackwhite.js?${sbPID}"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="newShowPortal">
    <div id="config-components">
        <ul>
            <li><a href="#core-component-group1">Add New Show</a></li>
        </ul>

    <div id="core-component-group1" class="tab-pane active component-group">

    <div id="displayText">aoeu</div>
    <br />

    <form id="addShowForm" method="post" action="${sbRoot}/home/addShows/addNewShow" accept-charset="utf-8">

    <fieldset class="sectionwrap">
        <legend class="legendStep">Find a show on theTVDB</legend>

        <div class="stepDiv">
            <input type="hidden" id="indexer_timeout" value="${sickbeard.INDEXER_TIMEOUT}" />

            % if use_provided_info:
                Show retrieved from existing metadata: <a href="${anon_url(sickbeard.indexerApi(provided_indexer).config['show_url'], provided_indexer_id)}">${provided_indexer_name}</a>
                <input type="hidden" id="indexerLang" name="indexerLang" value="en" />
                <input type="hidden" id="whichSeries" name="whichSeries" value="${provided_indexer_id}" />
                <input type="hidden" id="providedIndexer" name="providedIndexer" value="${provided_indexer}" />
                <input type="hidden" id="providedName" value="${provided_indexer_name}" />
            % else:
                <input type="text" id="nameToSearch" value="${default_show_name}" class="form-control form-control-inline input-sm input350" />
                &nbsp;&nbsp;
                <select name="indexerLang" id="indexerLangSelect" class="form-control form-control-inline input-sm bfh-languages" data-language="${sickbeard.INDEXER_DEFAULT_LANGUAGE}" data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}">
                </select><b>*</b>
                &nbsp;
                <select name="providedIndexer" id="providedIndexer" class="form-control form-control-inline input-sm">
                    <option value="0" ${('', 'selected="selected"')[provided_indexer == 0]}>All Indexers</option>
                    % for indexer in indexers:
                        <option value="${indexer}" ${('', 'selected="selected"')[provided_indexer == indexer]}>
                            ${indexers[indexer]}
                        </option>
                    % endfor
                </select>
                &nbsp;
                <input class="btn btn-inline" type="button" id="searchName" value="Search" />

                <br /><br />
                <b>*</b> This will only affect the language of the retrieved metadata file contents and episode filenames.<br />
                This <b>DOES NOT</b> allow SickRage to download non-english TV episodes!<br /><br />
                <div id="searchResults" style="height: 100%;"><br/></div>
            % endif

        </div>
    </fieldset>

    <fieldset class="sectionwrap">
        <legend class="legendStep">Pick the parent folder</legend>

        <div class="stepDiv">
            % if provided_show_dir:
                Pre-chosen Destination Folder: <b>${provided_show_dir}</b> <br />
                <input type="hidden" id="fullShowPath" name="fullShowPath" value="${provided_show_dir}" /><br />
            % else:
                <%include file="/inc_rootDirs.mako"/>
            % endif
        </div>
    </fieldset>

    <fieldset class="sectionwrap">
        <legend class="legendStep">Customize options</legend>
            <div class="stepDiv">
                <%include file="/inc_addShowOptions.mako"/>
            </div>
    </fieldset>

    % for curNextDir in other_shows:
    <input type="hidden" name="other_shows" value="${curNextDir}" />
    % endfor
    <input type="hidden" name="skipShow" id="skipShow" value="" />
    </form>

<br />

<div style="width: 100%; text-align: center;">
<input class="btn" type="button" id="addShowButton" value="Add Show" disabled="disabled" />
% if provided_show_dir:
<input class="btn" type="button" id="skipShowButton" value="Skip Show" />
% endif
</div>
</div></div></div></div>
</%block>
