<%inherit file="/layouts/main.mako"/>
<%!
    import datetime
    import locale
    import sickbeard
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
    from sickbeard.sbdatetime import sbdatetime, date_presets, time_presets
    from sickbeard import config
    from sickbeard import metadata
    from sickbeard.metadata.generic import GenericMetadata
%>
<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/configBackupRestore.js?${sbPID}"></script>
<script type="text/javascript" charset="utf-8">
    $('#backupDir').fileBrowser({ title: 'Select backup folder to save to', key: 'backupPath' });
    $('#backupFile').fileBrowser({ title: 'Select backup files to restore', key: 'backupFile', includeFiles: 1 });
    $('#config-components').tabs();
</script>
</%block>
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

<script type="text/javascript" src="${sbRoot}/js/config.js?${sbPID}"></script>

<div id="config">
    <div id="config-content">

        <form name="configForm" method="post" action="backuprestore">
            <div id="config-components">
                <ul>
                    <li><a href="#core-component-group1">Backup</a></li>
                    <li><a href="#core-component-group2">Restore</a></li>
                </ul>

                <div id="core-component-group1" class="component-group clearfix">
                    <div class="component-group-desc">
                        <h3>Backup</h3>
                        <p><b>Backup your main database file and config.</b></p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            Select the folder you wish to save your backup file to:

                            <br/><br/>

                            <input type="text" name="backupDir" id="backupDir" class="form-control input-sm input350" />
                            <input class="btn btn-inline" type="button" value="Backup" id="Backup" />

                            <br/>

                        </div>
                        <div class="Backup" id="Backup-result"></div>
                    </fieldset>

                </div><!-- /component-group1 //-->

                <div id="core-component-group2" class="component-group clearfix">
                    <div class="component-group-desc">
                        <h3>Restore</h3>
                        <p><b>Restore your main database file and config.</b></p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            Select the backup file you wish to restore:

                            <br/><br/>

                            <input type="text" name="backupFile" id="backupFile" class="form-control input-sm input350" />
                            <input class="btn btn-inline" type="button" value="Restore" id="Restore" />

                            <br/>

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
