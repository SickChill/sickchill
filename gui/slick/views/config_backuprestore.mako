<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<% indexer = 0 %>
% if sickbeard.INDEXER_DEFAULT:
    <% indexer = sickbeard.INDEXER_DEFAULT %>
% endif
<div id="config">
    <div id="config-content">

        <form name="configForm" method="post" action="backuprestore">
            <div id="config-components">
                <ul>
                    <li><a href="#backup">Backup</a></li>
                    <li><a href="#restore">Restore</a></li>
                </ul>

                <div id="backup" class="component-group clearfix">
                    <div class="component-group-desc">
                        <h3>Backup</h3>
                        <p><b>Backup your main database file and config.</b></p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            Select the folder you wish to save your backup file to:

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
                        <h3>Restore</h3>
                        <p><b>Restore your main database file and config.</b></p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            Select the backup file you wish to restore:

                            <br><br>

                            <input type="text" name="backupFile" id="backupFile" class="form-control input-sm input350" autocapitalize="off" />
                            <input class="btn btn-inline" type="button" value="Restore" id="Restore" />

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
