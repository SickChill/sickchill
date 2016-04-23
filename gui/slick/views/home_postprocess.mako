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

    <form name="processForm" method="post" action="processEpisode" style="line-height: 40px;">
        <div class="row">
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <b>${_('Enter the folder containing the episode')}:</b>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <input type="text" name="proc_dir" id="episodeDir" class="form-control form-control-inline input-sm" autocapitalize="off" title="directory"/>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <b>${_('Process Method to be used')}:</b>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <select name="process_method" id="process_method" class="form-control form-control-inline input-sm" title="process method">
                    <% process_method_text = {'copy': _('Copy'), 'move': _('Move'), 'hardlink': _('Hard Link'), 'symlink' : _('Symbolic Link')} %>
                    % for curAction in process_method_text:
                        <option value="${curAction}" ${('', 'selected="selected"')[sickbeard.PROCESS_METHOD == curAction]}>${process_method_text[curAction]}</option>
                    % endfor
                </select>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <b>${_('Force already Post Processed Dir/Files')}:</b>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <input id="force" name="force" type="checkbox">
            </div>
        </div>
        <div class="row">
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <b>${_('Mark Dir/Files as priority download')}:</b>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <input id="is_priority" name="is_priority" type="checkbox">
                <span style="line-height: 0; font-size: 12px;"><i>&nbsp;${_('(Check it to replace the file even if it exists at higher quality)')}</i></span>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <b>${_('Delete files and folders')}:</b>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                <input id="delete_on" name="delete_on" type="checkbox">
                <span style="line-height: 0; font-size: 12px;"><i>&nbsp;${_('(Check it to delete files and folders like auto processing)')}</i></span>
            </div>
        </div>
        % if sickbeard.USE_FAILED_DOWNLOADS:
            <div class="row">
                <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                    <b>${_('Mark download as failed')}:</b>
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
</%block>
