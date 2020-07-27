<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-8 col-lg-offset-2 col-md-10 col-md-offset-1">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif

            <form name="processForm" method="post" action="processEpisode" style="line-height: 40px;">
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b class="pull-lg-right pull-md-right pull-sm-right">${_('Enter the folder containing the episode')}</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input type="text" name="proc_dir" id="episodeDir" class="form-control form-control-inline input-sm input250" autocapitalize="off" title="directory"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b class="pull-lg-right pull-md-right pull-sm-right">${_('Process Method to be used')}</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <select name="process_method" id="process_method" class="form-control form-control-inline input-sm" title="process method">
                            <% process_method_text = {'copy': _('Copy'), 'move': _('Move'), 'hardlink': _('Hard Link'), 'symlink' : _('Symbolic Link'), 'symlink_reversed' : _('Symbolic Link Reversed')} %>
                            % for curAction in process_method_text:
                                <option value="${curAction}" ${('', 'selected="selected"')[settings.PROCESS_METHOD == curAction]}>${process_method_text[curAction]}</option>
                            % endfor
                        </select>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b class="pull-lg-right pull-md-right pull-sm-right">${_('Force already Post Processed Dir/Files')}</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="force" name="force" type="checkbox">
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b class="pull-lg-right pull-md-right pull-sm-right">${_('Mark Dir/Files as priority download')}</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="is_priority" name="is_priority" type="checkbox">
                        <span style="line-height: 0; font-size: 12px;"><i>&nbsp;${_('(Check it to replace the file even if it exists at higher quality)')}</i></span>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b class="pull-lg-right pull-md-right pull-sm-right">${_('Delete files and folders')}</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="delete_on" name="delete_on" type="checkbox">
                        <span style="line-height: 0; font-size: 12px;"><i>&nbsp;${_('(Check it to delete files and folders like auto processing)')}</i></span>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b class="pull-lg-right pull-md-right pull-sm-right">${_('Don\'t use processing queue')}</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="force_next" name="force_next" type="checkbox">
                        <span style="line-height: 0; font-size: 12px;"><i>${_('(If checked this will return the result of the process here, but may be slow!)')}</i></span>
                    </div>
                </div>
                % if settings.USE_FAILED_DOWNLOADS:
                    <div class="row">
                        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                            <b class="pull-lg-right pull-md-right pull-sm-right">${_('Mark download as failed')}</b>
                        </div>
                        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                            <input id="failed" name="failed" type="checkbox">
                        </div>
                    </div>
                % endif
                <div class="row">
                    <div class="col-md-12">
                        <input id="submit" class="btn" type="submit" value="${_('Process')}" />
                    </div>
                </div>
            </form>
        </div>
    </div>
</%block>
