<%inherit file="/layouts/config.mako"/>
<%!
    from sickchill import oldbeard
%>

<%block name="tabs">
    <li><a href="#backup">${_('Backup')}</a></li>
    <li><a href="#restore">${_('Restore')}</a></li>
</%block>

<%block name="pages">
    <form method="post" action="backuprestore">

        <!-- /component-group1 //-->
        <div id="backup" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Backup')}</h3>
                    <p><b>${_('Backup your main database file and config.')}</b></p>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-md-12">
                                <div class="row">
                                    <div class="col-md-12">
                                        ${_('Select the folder you wish to save your backup file to')}:
                                    </div>
                                    <div class="col-md-12">
                                        <input type="text" name="backupDir" id="backupDir" class="form-control input-sm input350" autocapitalize="off"  title="Backup directory"/>
                                        <input class="btn btn-inline" type="button" value="Backup" id="Backup" />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="Backup" id="Backup-result"></div>
                    </fieldset>
                </div>
            </div>
        </div>

        <!-- /component-group2 //-->
        <div id="restore" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Restore')}</h3>
                    <p><b>${_('Restore your main database file and config.')}</b></p>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-md-12">
                                <div class="row">
                                    <div class="col-md-12">
                                        ${_('Select the backup file you wish to restore')}:
                                    </div>
                                    <div class="col-md-12">
                                        <input type="text" name="backupFile" id="backupFile" class="form-control input-sm input350" autocapitalize="off"  title="Backup directory"/>
                                        <input class="btn btn-inline" type="button" value="${_('Restore')}" id="Restore" />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="Restore" id="Restore-result"></div>
                    </fieldset>
                </div>
            </div>
        </div>
    </form>
</%block>

<!-- Disable save button -->
<%block name="saveButton"/>
