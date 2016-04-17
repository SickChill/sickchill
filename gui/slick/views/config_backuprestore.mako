<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="content">
<% indexer = 0 %>
% if sickbeard.INDEXER_DEFAULT:
    <% indexer = sickbeard.INDEXER_DEFAULT %>
% endif
<div id="config">
    <div id="config-content">
        % if not header is UNDEFINED:
            <h1 class="header">${header}</h1>
        % else:
            <h1 class="title">${title}</h1>
        % endif

        <form name="configForm" method="post" action="backuprestore">
            <div id="config-components">
                <ul>
                    <li><a href="#backup">${_('Backup')}</a></li>
                    <li><a href="#restore">${_('Restore')}</a></li>
                </ul>

                <div id="backup" class="component-group clearfix">
                    <div class="component-group-desc">
                        <h3>${_('Backup')}</h3>
                        <p><b>${_('Backup your main database file and config.')}</b></p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            ${_('Select the folder you wish to save your backup file to')}:

                            <br><br>

                            <input type="text" name="backupDir" id="backupDir" class="form-control input-sm input350" autocapitalize="off" />
                            <input class="btn btn-inline" type="button" value="Backup" id="Backup" />

                            <br>

                        </div>
                        <div class="Backup" id="Backup-result"></div>
                    </fieldset>

                </div><!-- /component-group1 //-->

                <div id="restore" class="component-group clearfix">
                    <div class="component-group-desc">
                        <h3>${_('Restore')}</h3>
                        <p><b>${_('Restore your main database file and config.')}</b></p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            ${_('Select the backup file you wish to restore')}:

                            <br><br>

                            <input type="text" name="backupFile" id="backupFile" class="form-control input-sm input350" autocapitalize="off" />
                            <input class="btn btn-inline" type="button" value="${_('Restore')}" id="Restore" />

                            <br>

                        </div>
                        <div class="Restore" id="Restore-result"></div>
                    </fieldset>
                </div><!-- /component-group2 //-->
            </div><!-- /config-components -->
        </form>
    </div>
</div>

<div class="clearfix"></div>
</%block>
