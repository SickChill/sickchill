<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="content">
<div id="content800">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="postProcess">
    <form name="processForm" method="post" action="processEpisode" style="line-height: 40px;">
    <table>
        <input type="hidden" id="proc_type" name="proc_type" value="manual">
        <tr>
            <td style="padding-right:10px;">
                <b>${_('Enter the folder containing the episode')}:</b>
            </td>
            <td>
                <input type="text" name="proc_dir" id="episodeDir" class="form-control form-control-inline input-sm input350" autocapitalize="off" />
            </td>
        </tr>
        <tr>
            <td>
                <b>${_('Process Method to be used')}:</b>
            </td>
            <td>
                <select name="process_method" id="process_method" class="form-control form-control-inline input-sm" >
                <% process_method_text = {'copy': "Copy", 'move': "Move", 'hardlink': "Hard Link", 'symlink' : "Symbolic Link"} %>
                % for cur_action in ('copy', 'move', 'hardlink', 'symlink'):
                    <option value="${cur_action}" ${('', 'selected="selected"')[sickbeard.PROCESS_METHOD == cur_action]}>${process_method_text[cur_action]}</option>
                % endfor
                </select>
            </td>
        </tr>
        <tr>
            <td>
                <b>${_('Force already Post Processed Dir/Files')}:</b>
            </td>
            <td>
                <input id="force" name="force" type="checkbox">
            </td>
        </tr>
        <tr>
            <td>
                <b>${_('Mark Dir/Files as priority download')}:</b>
            </td>
            <td>
                <input id="is_priority" name="is_priority" type="checkbox">
                <span style="line-height: 0; font-size: 12px;"><i>&nbsp;${_('(Check it to replace the file even if it exists at higher quality)')}</i></span>
            </td>
        </tr>
        <tr>
            <td>
                <b>${_('Delete files and folders')}:</b>
            </td>
            <td>
                <input id="delete_on" name="delete_on" type="checkbox">
                <span style="line-height: 0; font-size: 12px;"><i>&nbsp;${_('(Check it to delete files and folders like auto processing)')}</i></span>
            </td>
        </tr>
        % if sickbeard.USE_FAILED_DOWNLOADS:
        <tr>
            <td>
                <b>${_('Mark download as failed')}:</b>
            </td>
            <td>
                <input id="failed" name="failed" type="checkbox">
            </td>
        </tr>
        % endif
    </table>
        <input id="submit" class="btn" type="submit" value="${_('Process')}" />
    </form>
</div>
</%block>
