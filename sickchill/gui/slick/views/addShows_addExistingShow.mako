<%inherit file="/layouts/main.mako"/>
<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/blackwhite.js')}"></script>
</%block>
<%block name="content">
<div class="col-md-12">
    <div class="row">
        <div class="col-md-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div id="config-components">
                <ul>
                    <li><a href="#core-component-group1">${_('Add Existing Show')}</a></li>
                </ul>

                <div id="core-component-group1" class="tab-pane active component-group">

                    <form id="addShowForm" method="post" action="${scRoot}/addShows/addExistingShows" accept-charset="utf-8">

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
                        <div class="row">
                            <div class="col-md-12">
                                <p>${_('SickChill can add existing shows, using the current options, by using locally stored NFO/XML metadata to eliminate user interaction. If you would rather have SickChill prompt you to customize each show, then use the checkbox below.')}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <input type="checkbox" name="promptForSettings" id="promptForSettings" />
                                <label for="promptForSettings">${_('Prompt me to set settings for each show')}</label>
                            </div>
                        </div>
                        <br>
                        <div class="row">
                            <div class="col-md-12">
                                <h5>${_("Displaying folders within these directories which aren't already added to SickChill")}</h5>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <ul id="rootDirStaticList"></ul>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div id="tableDiv" class="horizontal-scroll"></div>
                            </div>
                        </div>
                        <br/>
                        <div class="row">
                            <div class="col-md-12">
                                <input class="btn btn-primary" type="button" value="${_('Submit')}" id="submitShowDirs" />
                            </div>
                        </div>

                    </form>

                </div>
            </div>
        </div>
    </div>
</div>
</%block>
