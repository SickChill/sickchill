<%inherit file="/layouts/config.mako"/>
<%!
    import os.path
    import datetime
    import platform
    from sickchill.oldbeard.common import MULTI_EP_STRINGS
    from sickchill.settings import unpackStrings
    from sickchill import settings
    from sickchill.oldbeard import naming
%>

<%block name="tabs">
    <li><a href="#post-processing">${_('Post-Processing')}</a></li>
    <li><a href="#episode-naming">${_('Episode Naming')}</a></li>
    <li><a href="#metadata">${_('Metadata')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="savePostProcessing" method="post">

        <!-- /Post-Processing //-->
        <div id="post-processing" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <h3>${_('Post-Processing')}</h3>
                        <p>${_('Settings that dictate how SickChill should process completed downloads.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" name="process_automatically" id="process_automatically" ${('', 'checked="checked"')[bool(settings.PROCESS_AUTOMATICALLY)]}/>
                                        <label for="process_automatically">${_('enable the automatic post processor to scan and process any files in your Post Processing Dir')}?</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <span><b>${_('note')}:</b>&nbsp;${_('do not use if you use an external Post Processing script')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Post Processing Dir')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="text" name="tv_download_dir" id="tv_download_dir" value="${settings.TV_DOWNLOAD_DIR}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <span>${_('the folder where your download client puts the completed TV downloads.')}</span>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <span><b>${_('note')}:</b>&nbsp;${_('please use separate downloading and completed folders in your download client if possible.')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Processing Method')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <select name="process_method" id="process_method" class="form-control input-sm input350" title="process_method">
                                            <% process_method_text = {'copy': "Copy", 'move': "Move", 'hardlink': "Hard Link", 'symlink' : "Symbolic Link", 'symlink_reversed' : "Symbolic Link Reversed"} %>
                                            % for curAction in ('copy', 'move', 'hardlink', 'symlink', 'symlink_reversed'):
                                                <option value="${curAction}" ${('', 'selected="selected"')[settings.PROCESS_METHOD == curAction]}>${process_method_text[curAction]}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <span>${_('what method should be used to put files into the library?')}</span>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <span><b>${_('note')}:</b>&nbsp;${_('if you keep seeding torrents after they finish, please avoid the \'move\' processing method to prevent errors.')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Auto Post-Processing Frequency')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="number" min="10" step="1" name="autopostprocessor_frequency" id="autopostprocessor_frequency" value="${settings.AUTOPOSTPROCESSOR_FREQUENCY}" class="form-control input-sm input75" title="autopostprocessor_frequency"/>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label for="autopostprocessor_frequency" class="component-desc">${_('time in minutes to check for new files to auto post-process (min 10)')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Postpone post processing')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" name="postpone_if_sync_files" id="postpone_if_sync_files" ${('', 'checked="checked"')[bool(settings.POSTPONE_IF_SYNC_FILES)]}/>
                                <label for="postpone_if_sync_files">${_('wait to process a folder if sync files are present.')}</label>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Sync File Extensions')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="text" name="sync_files" id="sync_files" value="${settings.SYNC_FILES}" class="form-control input-sm input350" autocapitalize="off" title="sync_files"/>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <span class="component-desc">${_('comma separated list of extensions or filename globs SickChill ignores when Post Processing')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Rename Episodes')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" name="rename_episodes" id="rename_episodes" ${('', 'checked="checked"')[bool(settings.RENAME_EPISODES)]}/>
                                <label for="rename_episodes">${_('rename episode using the Episode Naming settings?')}</label>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Create missing show directories')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" name="create_missing_show_dirs" id="create_missing_show_dirs" ${('', 'checked="checked"')[bool(settings.CREATE_MISSING_SHOW_DIRS)]}/>
                                <label for="create_missing_show_dirs">${_('create missing show directories when they get deleted')}</label>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Add shows without directory')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" name="add_shows_wo_dir" id="add_shows_wo_dir" ${('', 'checked="checked"')[bool(settings.ADD_SHOWS_WO_DIR)]}/>
                                <label for="add_shows_wo_dir">${_('add shows without creating a directory (not recommended)')}</label>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Move associated files')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" class="enabler" name="move_associated_files" id="move_associated_files" ${('', 'checked="checked"')[bool(settings.MOVE_ASSOCIATED_FILES)]}/>
                                <label for="move_associated_files">${_('move associated (srt/srr/sfv/etc) files while post processing?')}</label>
                            </div>
                        </div>

                        <div class="field-pair row" id="content_move_associated_files">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Rename .nfo file')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" name="nfo_rename" id="nfo_rename" ${('', 'checked="checked"')[bool(settings.NFO_RENAME)]}/>
                                <label for="nfo_rename">${_('rename the original .nfo file to .nfo-orig to avoid conflicts?')}</label>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Associated file extensions')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="text" name="allowed_extensions" id="allowed_extensions" value="${settings.ALLOWED_EXTENSIONS}" class="form-control input-sm input350" autocapitalize="off" />
                                        <label for="allowed_extensions">${_('comma separated list of associated file extensions SickChill should keep while post processing.')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label for="allowed_extensions">${_('leaving it empty means no associated files will be post processed')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Delete non associated files')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" name="delete_non_associated_files" id="delete_non_associated_files" ${('', 'checked="checked"')[bool(settings.DELETE_NON_ASSOCIATED_FILES)]}/>
                                <label for="delete_non_associated_files">${_('delete non associated files while post processing?')}</label>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Change File Date')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" name="airdate_episodes" id="airdate_episodes" ${('', 'checked="checked"')[bool(settings.AIRDATE_EPISODES)]}/>
                                        <label for="airdate_episodes">${_('set last modified file date to the date that the episode aired?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b> ${_('some systems may ignore this feature.')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Timezone for File Date')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <select name="file_timestamp_timezone" id="file_timestamp_timezone" class="form-control input-sm input350">
                                            % for curTimezone in (_('local'), _('network')):
                                                <option value="${curTimezone}" ${('', 'selected="selected"')[settings.FILE_TIMESTAMP_TIMEZONE == curTimezone]}>${curTimezone}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label for="file_timestamp_timezone">${_('what timezone should be used to change File Date?')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <fieldset class="component-group-list">
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Unpack')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <label for="unpack" class="component-desc">
                                        ${_('What to do with archived releases found in your <i>TV Download Dir</i>?')}
                                    </label>
                                </div>

                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select name="unpack" id="unpack" class="form-control input-sm input350" title="unpack">
                                              % for value, description in unpackStrings.items():
                                                <option value="${value}" ${('', 'selected="selected"')[int(settings.UNPACK) == value]}>
                                                    ${description}
                                                </option>
                                              % endfor
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span><b>${_('note')}:</b>&nbsp;${_('\'Unpack\' only works with RAR archives')}</span>
                                        </div>
                                    </div>
                                    % if platform.system() in ('Windows', 'Microsoft'):
                                        <div class="row">
                                            <div class="col-md-12">
                                                <span><b>${_('Windows')}:</b>&nbsp;${_('WinRar is required on windows')}</span>
                                            </div>
                                        </div>
                                    % endif
                                </div>
                            </div>
                            <div id="content_unpack">
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                        <label class="component-title">${_('Unpack Directory')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="unpack_dir" id="unpack_dir" value="${settings.UNPACK_DIR}" class="form-control
                                                input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="unpack_dir">${_('Choose a path to unpack files, leave blank to unpack in download dir')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                        <label class="component-title">${_('Unrar Location')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="unrar_tool" id="unrar_tool" value="${settings.UNRAR_TOOL}" class="form-control
                                                input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="unrar_tool">${_('add the path to unrar if it is not in the system path')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                        <label class="component-title">${_('Unar Tool')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="unar_tool" id="unar_tool" value="${settings.UNAR_TOOL}" class="form-control
                                                input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="unar_tool">${_('add the path to an unar tool if it is not in the system path')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                        <label class="component-title">${_('BSDTar Tool')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="bsdtar_tool" id="bsdtar_tool" value="${settings.BSDTAR_TOOL}" class="form-control
                                                input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="bsdtar_tool">${_('add the path to an bsdtar tool if it is not in the system path')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                        <label class="component-title">${_('Delete RAR contents')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="checkbox" name="del_rar_contents" id="del_rar_contents" ${('', 'checked="checked"')[bool(settings.DELRARCONTENTS)]}/>
                                                <label for="del_rar_contents">${_('delete content of RAR files, even if Process Method not set to move?')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label><b>${_('note')}:</b>&nbsp;${_('only working with RAR archive')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </fieldset>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Don\'t delete empty folders')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" name="no_delete" id="no_delete" ${('', 'checked="checked"')[bool(settings.NO_DELETE)]}/>
                                        <label for="no_delete">${_('leave empty folders when Post Processing?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b>&nbsp;${_('can be overridden using manual Post Processing')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>


                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Follow symbolic-links')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" name="processor_follow_symlinks" id="processor_follow_symlinks"
                                            ${('', 'checked="checked"')[bool(settings.PROCESSOR_FOLLOW_SYMLINKS)]}/>
                                        <label for="processor_follow_symlinks">${_('follow down symbolic links in download directory?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('warning')}:</b>&nbsp;${_('<b>EXPERTS ONLY.</b><br>'
                                                'Enable only if you know what <b>circular symbolic links</b> are,<br>'
                                                'and can <b>verify that you have none</b>.')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Use icacls')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" name="use_icacls" id="use_icacls" ${('', 'checked="checked"')[bool(settings.USE_ICACLS)]}/>
                                        <label for="use_icacls">${_('Windows only')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label>${_('sets video permissions after using the move method in post processing')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Extra Scripts')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="text" name="extra_scripts" value="${'|'.join(settings.EXTRA_SCRIPTS)}" class="form-control input-sm input350" autocapitalize="off"  title="extra_script"/>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label>
                                            ${_('see')}
                                            <a href="https://github.com/SickChill/SickChill/wiki/Post-Processing#extra-scripts">
                                                <span style="color:red;">Wiki</span>
                                            </a>${_('for script arguments description and usage.')}
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>
        </div>

        <!-- /Episode-Naming //-->
        <div id="episode-naming" class="component-group">

            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <h3>${_('Episode Naming')}</h3>
                        <p>${_('How SickChill will name and sort your episodes.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label for="name_presets" class="component-title">${_('Name Pattern')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <select id="name_presets" class="form-control input-sm input350" title="name_presets">
                                    <% is_custom = True %>
                                    % for cur_preset in naming.name_presets:
                                    <% tmp = naming.test_name(cur_preset, anime_type=3) %>
                                    % if cur_preset == settings.NAMING_PATTERN:
                                        <% is_custom = False %>
                                    % endif
                                        <option id="${cur_preset}" ${('', 'selected="selected"')[settings.NAMING_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                    % endfor
                                    <option id="${settings.NAMING_PATTERN}" ${('', 'selected="selected"')[bool(is_custom)]}>Custom...</option>
                                </select>
                            </div>
                        </div>

                        <div id="content_name_presets">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12"></div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="naming_pattern" id="naming_pattern" value="${settings.NAMING_PATTERN}" class="form-control input-sm input350" autocapitalize="off" title="naming_pattern"/>
                                            <span class="displayshow-icon-legend" id="show_naming_key" title="${_('Toggle Naming Legend')}" class="legend"></span>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label><b>${_('note')}:</b>&nbsp;${_('don\'t forget to add quality pattern. Otherwise after post-processing the episode will have UNKNOWN quality')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="naming_key" style="display: none;">
                                <div class="horizontal-scroll">
                                    <table class="Key">
                                        <thead>
                                            <tr>
                                                <th class="align-right">${_('Meaning')}</th>
                                                <th>${_('Pattern')}</th>
                                                <th>${_('Result')}</th>
                                            </tr>
                                        </thead>
                                        <tfoot>
                                            <tr>
                                                <th colspan="3">${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}</th>
                                            </tr>
                                        </tfoot>
                                        <tbody>
                                            <tr>
                                                <td class="align-right"><b>${_('Show Name')}:</b></td>
                                                <td>%SN</td>
                                                <td>${_('Show Name')}</td>
                                            </tr>
                                            <tr class="even">
                                                <td>&nbsp;</td>
                                                <td>%S.N</td>
                                                <td>${_('Show.Name')}</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%S_N</td>
                                                <td>${_('Show_Name')}</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><b>${_('Season Number')}:</b></td>
                                                <td>%S</td>
                                                <td>2</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%0S</td>
                                                <td>02</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><b>${_('XEM Season Number')}:</b></td>
                                                <td>%XS</td>
                                                <td>2</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%0XS</td>
                                                <td>02</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><b>${_('Episode Number')}:</b></td>
                                                <td>%E</td>
                                                <td>3</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%0E</td>
                                                <td>03</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><b>${_('XEM Episode Number')}:</b></td>
                                                <td>%XE</td>
                                                <td>3</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%0XE</td>
                                                <td>03</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><b>${_('Episode Name')}:</b></td>
                                                <td>%EN</td>
                                                <td>${_('Episode Name')}</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%E.N</td>
                                                <td>${_('Episode.Name')}</td>
                                            </tr>
                                            <tr class="even">
                                                <td>&nbsp;</td>
                                                <td>%E_N</td>
                                                <td>${_('Episode_Name')}</td>
                                            </tr>
                                            <tr>
                                                <td class="align-right"><b>${_('Air Date')}:</b></td>
                                                <td>%M</td>
                                                <td>${datetime.date.today().month}</td>
                                            </tr>
                                            <tr class="even">
                                                <td>&nbsp;</td>
                                                <td>%D</td>
                                                <td>${datetime.date.today().day}</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%Y</td>
                                                <td>${datetime.date.today().year}</td>
                                            </tr>
                                            <tr>
                                                <td class="align-right"><b>${_('Post-Processing Date')}:</b></td>
                                                <td>%CM</td>
                                                <td>${datetime.date.today().month}</td>
                                            </tr>
                                            <tr class="even">
                                                <td>&nbsp;</td>
                                                <td>%CD</td>
                                                <td>${datetime.date.today().day}</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%CY</td>
                                                <td>${datetime.date.today().year}</td>
                                            </tr>
                                            <tr>
                                                <td class="align-right"><b>${_('Quality')}:</b></td>
                                                <td>%QN</td>
                                                <td>720p BluRay</td>
                                            </tr>
                                            <tr class="even">
                                                <td>&nbsp;</td>
                                                <td>%Q.N</td>
                                                <td>720p.BluRay</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%Q_N</td>
                                                <td>720p_BluRay</td>
                                            </tr>
                                            <tr>
                                                <td class="align-right"><b>${_('Scene Quality')}:</b></td>
                                                <td>%SQN</td>
                                                <td>720p HDTV x264</td>
                                            </tr>
                                            <tr class="even">
                                                <td>&nbsp;</td>
                                                <td>%SQ.N</td>
                                                <td>720p.HDTV.x264</td>
                                            </tr>
                                            <tr>
                                                <td>&nbsp;</td>
                                                <td>%SQ_N</td>
                                                <td>720p_HDTV_x264</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="Multi-EP style is ignored"></i> <b>${_('Release Name')}:</b></td>
                                                <td>%RN</td>
                                                <td>${_('Show.Name')}.S02E03.HDTV.XviD-RLSGROUP</td>
                                            </tr>
                                            <tr>
                                                <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="'${_('SickChill\' is used in place of RLSGROUP if it could not be properly detected')}"></i> <b>${_('Release Group')}:</b></td>
                                                <td>%RG</td>
                                                <td>RLSGROUP</td>
                                            </tr>
                                            <tr class="even">
                                                <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('If episode is proper/repack add \'proper\' to name.')}"></i> <b>${_('Release Type')}:</b></td>
                                                <td>%RT</td>
                                                <td>PROPER</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Multi-Episode Style')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <select id="naming_multi_ep" name="naming_multi_ep" class="form-control input-sm input350" title="naming_multi_ep">
                                    % for cur_multi_ep in sorted(MULTI_EP_STRINGS.items(), key=lambda x: x[1]):
                                        <option value="${cur_multi_ep[0]}" ${('', 'selected="selected"')[cur_multi_ep[0] == settings.NAMING_MULTI_EP]}>${cur_multi_ep[1]}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>

                        <div id="naming_example_div">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3>${_('Single-EP Sample')}:</h3>
                                    <div class="example">
                                        <span class="jumbo" id="naming_example">&nbsp;</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="naming_example_multi_div">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3>${_('Multi-EP sample')}:</h3>
                                    <div class="example">
                                        <span class="jumbo" id="naming_example_multi">&nbsp;</span>
                                    </div>
                                </div>
                            </div>
                            <br/>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Strip Show Year')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" id="naming_strip_year"  name="naming_strip_year" ${('', 'checked="checked"')[bool(settings.NAMING_STRIP_YEAR)]}/>
                                        <label for="naming_strip_year">${_('remove the TV show\'s year when renaming the file?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label>${_('only applies to shows that have year inside parentheses')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Custom Air-By-Date')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" class="enabler" id="naming_custom_abd" name="naming_custom_abd" ${('', 'checked="checked"')[bool(settings.NAMING_CUSTOM_ABD)]}/>
                                <label for="naming_custom_abd">${_('name air-by-date shows differently than regular shows?')}</label>
                            </div>
                        </div>

                        <div id="content_naming_custom_abd">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Name Pattern')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <select id="name_abd_presets" class="form-control input-sm input350" title="name_adb_presets">
                                        <% is_abd_custom = True %>
                                        % for cur_preset in naming.name_abd_presets:
                                        <% tmp = naming.test_name(cur_preset) %>
                                        % if cur_preset == settings.NAMING_ABD_PATTERN:
                                            <% is_abd_custom = False %>
                                        % endif
                                            <option id="${cur_preset}" ${('', 'selected="selected"')[settings.NAMING_ABD_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                        % endfor
                                        <option id="${settings.NAMING_ABD_PATTERN}" ${('', 'selected="selected"')[bool(is_abd_custom)]}>Custom...</option>
                                    </select>
                                </div>
                            </div>

                            <!-- naming_abd_custom -->
                            <div id="naming_abd_custom">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12"></div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <input type="text" name="naming_abd_pattern" id="naming_abd_pattern" value="${settings.NAMING_ABD_PATTERN}"
                                               class="form-control input-sm input350" autocapitalize="off" title="naming_abd_pattern"/>
                                        <span class="displayshow-icon-legend" id="show_naming_abd_key" title="${_('Toggle ABD Naming Legend')}" class="legend"></span>
                                    </div>
                                </div>

                                <div id="naming_abd_key" style="display: none;">
                                    <div class="horizontal-scroll">
                                        <table class="Key">
                                            <thead>
                                                <tr>
                                                    <th class="align-right">${_('Meaning')}</th>
                                                    <th>${_('Pattern')}</th>
                                                    <th>${_('Result')}</th>
                                                </tr>
                                            </thead>
                                            <tfoot>
                                                <tr>
                                                    <th colspan="3">${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}</th>
                                                </tr>
                                            </tfoot>
                                            <tbody>
                                                <tr>
                                                    <td class="align-right"><b>${_('Show Name')}:</b></td>
                                                    <td>%SN</td>
                                                    <td>${_('Show Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%S.N</td>
                                                    <td>${_('Show.Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%S_N</td>
                                                    <td>${_('Show_Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Regular Air Date')}:</b></td>
                                                    <td>%AD</td>
                                                    <td>2010 03 09</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%A.D</td>
                                                    <td>2010.03.09</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%A_D</td>
                                                    <td>2010_03_09</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%A-D</td>
                                                    <td>2010-03-09</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Episode Name')}:</b></td>
                                                    <td>%EN</td>
                                                    <td>${_('Episode Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%E.N</td>
                                                    <td>${_('Episode.Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%E_N</td>
                                                    <td>${_('Episode_Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Quality')}:</b></td>
                                                    <td>%QN</td>
                                                    <td>720p BluRay</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%Q.N</td>
                                                    <td>720p.BluRay</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%Q_N</td>
                                                    <td>720p_BluRay</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Year')}:</b></td>
                                                    <td>%Y</td>
                                                    <td>2010</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Month')}:</b></td>
                                                    <td>%M</td>
                                                    <td>3</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right">&nbsp;</td>
                                                    <td>%0M</td>
                                                    <td>03</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Day')}:</b></td>
                                                    <td>%D</td>
                                                    <td>9</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right">&nbsp;</td>
                                                    <td>%0D</td>
                                                    <td>09</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('Multi-EP style is ignored')}"></i> <b>${_('Release Name')}:</b></td>
                                                    <td>%RN</td>
                                                    <td>${_('Show.Name')}.2010.03.09.HDTV.XviD-RLSGROUP</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="'${_('SickChill\' is used in place of RLSGROUP if it could not be properly detected')}"></i> <b>${_('Release Group')}:</b></td>
                                                    <td>%RG</td>
                                                    <td>RLSGROUP</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('If episode is proper/repack add \'proper\' to name.')}"></i> <b>${_('Release Type')}:</b></td>
                                                    <td>%RT</td>
                                                    <td>PROPER</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <!-- /naming_abd_custom -->

                            <div id="naming_abd_example_div">
                                <div class="row">
                                    <div class="col-md-12">
                                        <h3>Sample:</h3>
                                        <div class="example">
                                            <span class="jumbo" id="naming_abd_example">&nbsp;</span>
                                        </div>
                                    </div>
                                </div>
                                <br>
                            </div>

                        </div>
                        <!-- /naming_abd_different -->

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Custom Sports')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" class="enabler" id="naming_custom_sports" name="naming_custom_sports" ${('', 'checked="checked"')[bool(settings.NAMING_CUSTOM_SPORTS)]}/>
                                <label for="naming_custom_sports" class="component-desc">${_('name sports shows differently than regular shows?')}</label>
                            </div>
                        </div>

                        <div id="content_naming_custom_sports">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Name Pattern')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <select id="name_sports_presets" class="form-control input-sm input350" title="name_sports_presets">
                                        <% is_sports_custom = True %>
                                        % for cur_preset in naming.name_sports_presets:
                                        <% tmp = naming.test_name(cur_preset) %>
                                        % if cur_preset == settings.NAMING_SPORTS_PATTERN:
                                            <% is_sports_custom = False %>
                                        % endif
                                            <option id="${cur_preset}" ${('', 'selected="selected"')[settings.NAMING_SPORTS_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                        % endfor
                                        <option id="${settings.NAMING_SPORTS_PATTERN}" ${('', 'selected="selected"')[bool(is_sports_custom)]}>Custom...</option>
                                    </select>
                                </div>
                            </div>

                            <div id="naming_sports_custom">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12"></div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <input type="text" name="naming_sports_pattern" id="naming_sports_pattern" value="${settings.NAMING_SPORTS_PATTERN}"
                                               class="form-control input-sm input350" autocapitalize="off" title="naming_sports_pattern" />
                                        <span class="displayshow-icon-legend" id="show_naming_sports_key" title="${_('Toggle Sports Naming Legend')}" class="legend"></span>
                                    </div>
                                </div>

                                <div id="naming_sports_key" style="display: none;">
                                    <div class="horizontal-scroll">
                                        <table class="Key">
                                            <thead>
                                                <tr>
                                                    <th class="align-right">${_('Meaning')}</th>
                                                    <th>${_('Pattern')}</th>
                                                    <th>${_('Result')}</th>
                                                </tr>
                                            </thead>
                                            <tfoot>
                                                <tr>
                                                    <th colspan="3">${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}</th>
                                                </tr>
                                            </tfoot>
                                            <tbody>
                                                <tr>
                                                    <td class="align-right"><b>${_('Show Name')}:</b></td>
                                                    <td>%SN</td>
                                                    <td>${_('Show Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%S.N</td>
                                                    <td>${_('Show.Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%S_N</td>
                                                    <td>${_('Show_Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Sports Air Date')}:</b></td>
                                                    <td>%AD</td>
                                                    <td>9 Mar 2011</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%A.D</td>
                                                    <td>9.Mar.2011</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%A_D</td>
                                                    <td>9_Mar_2011</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%A-D</td>
                                                    <td>9-Mar-2011</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Episode Name')}:</b></td>
                                                    <td>%EN</td>
                                                    <td>${_('Episode Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%E.N</td>
                                                    <td>${_('Episode.Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%E_N</td>
                                                    <td>${_('Episode_Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Quality')}:</b></td>
                                                    <td>%QN</td>
                                                    <td>720p BluRay</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%Q.N</td>
                                                    <td>720p.BluRay</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%Q_N</td>
                                                    <td>720p_BluRay</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Year')}:</b></td>
                                                    <td>%Y</td>
                                                    <td>2010</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Month')}:</b></td>
                                                    <td>%M</td>
                                                    <td>3</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right">&nbsp;</td>
                                                    <td>%0M</td>
                                                    <td>03</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Day')}:</b></td>
                                                    <td>%D</td>
                                                    <td>9</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right">&nbsp;</td>
                                                    <td>%0D</td>
                                                    <td>09</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('Multi-EP style is ignored')}"></i> <b>${_('Release Name')}:</b></td>
                                                    <td>%RN</td>
                                                    <td>${_('Show.Name')}.9th.Mar.2011.HDTV.XviD-RLSGROUP</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="'${_('SickChill\' is used in place of RLSGROUP if it could not be properly detected')}"></i> <b>${_('Release Group')}:</b></td>
                                                    <td>%RG</td>
                                                    <td>RLSGROUP</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('If episode is proper/repack add \'proper\' to name.')}"></i> <b>${_('Release Type')}:</b></td>
                                                    <td>%RT</td>
                                                    <td>PROPER</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <!-- /naming_sports_custom -->

                            <div id="naming_sports_example_div">
                                <div class="row">
                                    <div class="col-md-12">
                                        <h3>Sample:</h3>
                                        <div class="example">
                                            <span class="jumbo" id="naming_sports_example">&nbsp;</span>
                                        </div>
                                    </div>
                                </div>
                                <br/>
                            </div>

                        </div>
                        <!-- /naming_sports_different -->

                        <!-- naming_anime_custom -->
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <label class="component-title">${_('Custom Anime')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" class="enabler" id="naming_custom_anime" name="naming_custom_anime" ${('', 'checked="checked"')[bool(settings.NAMING_CUSTOM_ANIME)]}/>
                                <label for="naming_custom_anime">${_('name anime shows differently than regular shows?')}</label>
                            </div>
                        </div>

                        <div id="content_naming_custom_anime">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Name Pattern')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <select id="name_anime_presets" class="form-control input-sm input350">
                                        <% is_anime_custom = True %>
                                        % for cur_preset in naming.name_anime_presets:
                                        <% tmp = naming.test_name(cur_preset) %>
                                        % if cur_preset == settings.NAMING_ANIME_PATTERN:
                                            <% is_anime_custom = False %>
                                        % endif
                                            <option id="${cur_preset}" ${('', 'selected="selected"')[cur_preset == settings.NAMING_ANIME_PATTERN]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                        % endfor
                                        <option id="${settings.NAMING_ANIME_PATTERN}" ${('', 'selected="selected"')[bool(is_anime_custom)]}>Custom...</option>
                                    </select>
                                </div>
                            </div>

                            <div id="naming_anime_custom">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12"></div>
                                    <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                        <input type="text" name="naming_anime_pattern" id="naming_anime_pattern" value="${settings.NAMING_ANIME_PATTERN}"
                                               class="form-control input-sm input350" autocapitalize="off" title="naming_anime_pattern" />
                                        <span class="displayshow-icon-legend" id="show_naming_anime_key" title="${_('Toggle Anime Naming Legend')}" class="legend"></span>
                                    </div>
                                </div>

                                <div id="naming_anime_key" style="display: none;">
                                    <div class="horizontal-scroll">
                                        <table class="Key">
                                            <thead>
                                                <tr>
                                                    <th class="align-right">${_('Meaning')}</th>
                                                    <th>Pattern</th>
                                                    <th>${_('Result')}</th>
                                                </tr>
                                            </thead>
                                            <tfoot>
                                                <tr>
                                                    <th colspan="3">${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}</th>
                                                </tr>
                                            </tfoot>
                                            <tbody>
                                                <tr>
                                                    <td class="align-right"><b>${_('Show Name')}:</b></td>
                                                    <td>%SN</td>
                                                    <td>${_('Show Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%S.N</td>
                                                    <td>${_('Show.Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%S_N</td>
                                                    <td>${_('Show_Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Season Number')}:</b></td>
                                                    <td>%S</td>
                                                    <td>2</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%0S</td>
                                                    <td>02</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('>XEM Season Number')}:</b></td>
                                                    <td>%XS</td>
                                                    <td>2</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%0XS</td>
                                                    <td>02</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Episode Number')}:</b></td>
                                                    <td>%E</td>
                                                    <td>3</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%0E</td>
                                                    <td>03</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('XEM Episode Number')}:</b></td>
                                                    <td>%XE</td>
                                                    <td>3</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%0XE</td>
                                                    <td>03</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><b>${_('Episode Name')}:</b></td>
                                                    <td>%EN</td>
                                                    <td>${_('Episode Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%E.N</td>
                                                    <td>${_('Episode.Name')}</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%E_N</td>
                                                    <td>${_('Episode_Name')}</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><b>${_('Quality')}:</b></td>
                                                    <td>%QN</td>
                                                    <td>720p BluRay</td>
                                                </tr>
                                                <tr class="even">
                                                    <td>&nbsp;</td>
                                                    <td>%Q.N</td>
                                                    <td>720p.BluRay</td>
                                                </tr>
                                                <tr>
                                                    <td>&nbsp;</td>
                                                    <td>%Q_N</td>
                                                    <td>720p_BluRay</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('Multi-EP style is ignored')}"></i> <b>${_('Release Name')}:</b></td>
                                                    <td>%RN</td>
                                                    <td>${_('Show.Name')}.S02E03.HDTV.XviD-RLSGROUP</td>
                                                </tr>
                                                <tr>
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="'${_('SickChill\' is used in place of RLSGROUP if it could not be properly detected')}"></i> <b>${_('Release Group')}:</b></td>
                                                    <td>%RG</td>
                                                    <td>RLSGROUP</td>
                                                </tr>
                                                <tr class="even">
                                                    <td class="align-right"><i class="glyphicon glyphicon-info-sign" title="${_('If episode is proper/repack add \'proper\' to name.')}"></i> <b>${_('Release Type')}:</b></td>
                                                    <td>%RT</td>
                                                    <td>PROPER</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                            </div>
                            <!-- /naming_anime_custom -->

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Multi-Episode Style')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <select id="naming_anime_multi_ep" name="naming_anime_multi_ep" class="form-control input-sm input350" title="naming_anime_multi_ep">
                                        % for cur_multi_ep in sorted(MULTI_EP_STRINGS.items(), key=lambda x: x[1]):
                                            <option value="${cur_multi_ep[0]}" ${('', 'selected="selected" class="selected"')[cur_multi_ep[0] == settings.NAMING_ANIME_MULTI_EP]}>${cur_multi_ep[1]}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>

                            <div id="naming_example_anime_div">
                                <div class="row">
                                    <div class="col-md-12">
                                        <h3>${_('Single-EP Anime Sample')}:</h3>
                                        <div class="example">
                                            <span class="jumbo" id="naming_example_anime">&nbsp;</span>
                                        </div>
                                    </div>
                                </div>
                                <br>
                            </div>

                            <div id="naming_example_multi_anime_div">
                                <div class="row">
                                    <div class="col-md-12">
                                        <h3>${_('Multi-EP Anime sample')}:</h3>
                                        <div class="example">
                                            <span class="jumbo" id="naming_example_multi_anime">&nbsp;</span>
                                        </div>
                                    </div>
                                </div>
                                <br>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Add Absolute Number')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="radio" name="naming_anime" id="naming_anime" value="1" ${('', 'checked="checked"')[settings.NAMING_ANIME == 1]}/>
                                            <label for="naming_anime">${_('add the absolute number to the season/episode format?')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('only applies to anime. (eg. S15E45 - 310 vs S15E45)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Only Absolute Number')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="radio" name="naming_anime" id="naming_anime_only" value="2" ${('', 'checked="checked"')[settings.NAMING_ANIME == 2]}/>
                                            <label for="naming_anime_only">${_('replace season/episode format with absolute number')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('only applies to anime.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('No Absolute Number')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="radio" name="naming_anime" id="naming_anime_none" value="3" ${('', 'checked="checked"')[settings.NAMING_ANIME in (3, None)]}/>
                                            <label for="naming_anime_none">${_('don\'t include the absolute number')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('only applies to anime.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                        <!-- /naming_anime_different -->
                    </fieldset>

                </div>
            </div>
        </div>

        <!-- /Metadata// -->
        <div id="metadata" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <h3>${_('Metadata')}</h3>
                        <p>${_('The data associated to the data. These are files associated to a TV show in the form of images and text that, when supported, will enhance the viewing experience.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Metadata Type')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <select id="metadataType" class="form-control input-sm input350">
                                            % for (cur_name, cur_generator) in sorted(settings.metadata_provider_dict.items()):
                                                <option value="${cur_generator.get_id()}">${cur_name}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label for="metadataType">${_('toggle metadata options that you wish to be created')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('multiple targets may be used')}</b></label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Select Metadata')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                % for (cur_name, cur_generator) in settings.metadata_provider_dict.items():
                                    <%
                                        cur_metadata_inst = settings.metadata_provider_dict[cur_generator.name]
                                        cur_id = cur_generator.get_id()
                                    %>
                                    <div class="metadataDiv" id="${cur_id}">
                                        <div class="metadata_options_wrapper input350">
                                            <div class="metadata_options">
                                                <label for="${cur_id}_show_metadata">
                                                    <input type="checkbox" class="metadata_checkbox" id="${cur_id}_show_metadata" ${('', 'checked="checked"')[bool(cur_metadata_inst.show_metadata)]}/>
                                                    &nbsp;Show Metadata
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_show_metadata">${cur_metadata_inst.eg_show_metadata}</span>
                                                </label>
                                                <label for="${cur_id}_episode_metadata">
                                                    <input type="checkbox" class="metadata_checkbox" id="${cur_id}_episode_metadata" ${('', 'checked="checked"')[bool(cur_metadata_inst.episode_metadata)]}/>
                                                    &nbsp;Episode Metadata
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_episode_metadata">${cur_metadata_inst.eg_episode_metadata}</span>
                                                </label>
                                                <label for="${cur_id}_fanart">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_fanart" ${('', 'checked="checked"')[bool(cur_metadata_inst.fanart)]}/>
                                                    &nbsp;Show Fanart
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_fanart">${cur_metadata_inst.eg_fanart}</span>
                                                </label>
                                                <label for="${cur_id}_poster">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_poster" ${('', 'checked="checked"')[bool(cur_metadata_inst.poster)]}/>
                                                    &nbsp;Show Poster
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_poster">${cur_metadata_inst.eg_poster}</span>
                                                </label>
                                                <label for="${cur_id}_banner">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_banner" ${('', 'checked="checked"')[bool(cur_metadata_inst.banner)]}/>
                                                    &nbsp;Show Banner
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_banner">${cur_metadata_inst.eg_banner}</span>
                                                </label>
                                                <label for="${cur_id}_episode_thumbnails">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_episode_thumbnails" ${('', 'checked="checked"')[bool(cur_metadata_inst.episode_thumbnails)]}/>
                                                    &nbsp;Episode Thumbnails
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_episode_thumbnails">${cur_metadata_inst.eg_episode_thumbnails}</span>
                                                </label>
                                                <label for="${cur_id}_season_posters">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_posters" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_posters)]}/>
                                                    &nbsp;Season Posters
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_season_posters">${cur_metadata_inst.eg_season_posters}</span>
                                                </label>
                                                <label for="${cur_id}_season_banners">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_banners" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_banners)]}/>
                                                    &nbsp;Season Banners
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_season_banners">${cur_metadata_inst.eg_season_banners}</span>
                                                </label>
                                                <label for="${cur_id}_season_all_poster">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_all_poster" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_all_poster)]}/>
                                                    &nbsp;Season All Poster
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_season_all_poster">${cur_metadata_inst.eg_season_all_poster}</span>
                                                </label>
                                                <label for="${cur_id}_season_all_banner">
                                                    <input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_all_banner" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_all_banner)]}/>
                                                    &nbsp;Season All Banner
                                                    <br/>
                                                    &nbsp;<span id="${cur_id}_eg_season_all_banner">${cur_metadata_inst.eg_season_all_banner}</span>
                                                </label>
                                            </div>
                                        </div>
                                        <input type="hidden" name="${cur_id}_data" id="${cur_id}_data" value="${cur_metadata_inst.get_config()}" />
                                    </div>
                                % endfor
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>
        </div>
    </form>
</%block>
