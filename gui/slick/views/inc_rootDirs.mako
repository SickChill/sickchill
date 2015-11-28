<%
    import sickbeard

    if sickbeard.ROOT_DIRS:
        backend_pieces = sickbeard.ROOT_DIRS.split('|')
        backend_default = 'rd-' + backend_pieces[0]
        backend_dirs = backend_pieces[1:]
    else:
        backend_default = ''
        backend_dirs = []
%>

<span id="sampleRootDir"></span>

<input type="hidden" id="whichDefaultRootDir" value="${backend_default}"  autocapitalize="off" />
<div class="rootdir-selectbox">
    <select name="rootDir" id="rootDirs" size="6">
    % for cur_dir in backend_dirs:
        <option value="${cur_dir}">${cur_dir}</option>
    % endfor
    </select>
</div>
<div id="rootDirsControls" class="rootdir-controls">
    <input class="btn" type="button" id="addRootDir" value="New"  autocapitalize="off" />
    <input class="btn" type="button" id="editRootDir" value="Edit"  autocapitalize="off" />
    <input class="btn" type="button" id="deleteRootDir" value="Delete"  autocapitalize="off" />
    <input class="btn" type="button" id="defaultRootDir" value="Set as Default *"  autocapitalize="off" />
</div>
<input type="text" style="display: none" id="rootDirText"  autocapitalize="off" />
