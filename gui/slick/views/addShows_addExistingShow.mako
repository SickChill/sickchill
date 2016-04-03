<%inherit file="/layouts/main.mako"/>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/addShowOptions.js?${sbPID}"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
<h1 class="header">${header}</h1>
% else:
<h1 class="title">${title}</h1>
% endif

<div id="newShowPortal">
    <div id="config-components">
        <ul><li><a href="#core-component-group1">${_('Add Existing Show')}</a></li></ul>

    <div id="core-component-group1" class="tab-pane active component-group">

    <form id="addShowForm" method="post" action="${srRoot}/addShows/addNewShow" accept-charset="utf-8">

    <div id="tabs">
        <ul>
            <li><a href="#tabs-1">${_('Manage Directories')}</a></li>
            <li><a href="#tabs-2">${_('Customize Options')}</a></li>
        </ul>
        <div id="tabs-1" class="existingtabs">
            <%include file="/inc_rootDirs.mako"/>
        </div>
        <div id="tabs-2" class="existingtabs">
            <%include file="/inc_addShowOptions.mako"/>
        </div>
    </div>
    <br>

    <p>${_('''SickRage can add existing shows, using the current options, by using locally stored NFO/XML metadata to eliminate user interaction.
    If you would rather have SickRage prompt you to customize each show, then use the checkbox below.''')}</p>

    <p><input type="checkbox" name="promptForSettings" id="promptForSettings" /> <label for="promptForSettings">${_('Prompt me to set settings for each show')}</label></p>

    <hr />

    <p><b>${_('Displaying folders within these directories which aren\'t already added to SickRage:')}</b></p>

    <ul id="rootDirStaticList"><li></li></ul>
    <br>
    <div id="tableDiv"></div>
    <br>
    <br>
    <input class="btn btn-primary" type="button" value="Submit" id="submitShowDirs" />

    </form>

    </div>
    </div>
</div>
</%block>
