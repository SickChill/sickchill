<%
    from sickchill import settings

    if settings.ROOT_DIRS:
        backend_pieces = settings.ROOT_DIRS.split('|')
        backend_default = 'rd-' + backend_pieces[0]
        backend_dirs = backend_pieces[1:]
    else:
        backend_default = ''
        backend_dirs = []
%>

<div class="row">
    <div class="col-md-12">
        <span id="sampleRootDir"></span>

        <input type="hidden" id="whichDefaultRootDir" value="${backend_default}" />
        <div class="rootdir-selectbox">
            <select name="rootDir" id="rootDirs" size="6" title="Root directory">
                % for cur_dir in backend_dirs:
                    <option value="${cur_dir}">${cur_dir}</option>
                % endfor
            </select>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-md-12">
        <div id="rootDirsControls" class="rootdir-controls">
            <input class="btn" type="button" id="addRootDir" value="${_('New')}" />
            <input class="btn" type="button" id="editRootDir" value="${_('Edit')}" />
            <input class="btn" type="button" id="deleteRootDir" value="${_('Delete')}" />
            <input class="btn" type="button" id="defaultRootDir" value="${_('Set as default')} *" />
        </div>
        <input type="text" style="display: none" id="rootDirText" autocapitalize="off" />
    </div>
</div>
