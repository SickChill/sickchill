<%!
    from sickchill import settings
%>
<div class="row">
    <div class="col-lg-12 col-md-12 col-sm-12 col-xs-12 tex-center">
        <div class="text-center">
            % if settings.HOME_LAYOUT == 'poster':
                <span class="show-option">
                    <input id="filterShowName" class="form-control form-control-inline input-sm input200" type="search" placeholder="${_('Filter Show Name')}">
                </span>
            % endif
            % if settings.ROOT_DIRS:
                <span class="show-option">${_('Root')}:</span>
                <label>
                    <form method="post" action="" id="rootDirForm">
                        <select id="rootDirSelect" name="root" class="form-control form-control-inline input200" title="Root Select">
                        <option value="-1" ${('', 'selected="selected"')[selected_root == '-1']}>${_('All')}</option>
                        % for root_dir in settings.ROOT_DIRS.split('|')[1:]:
                            <option value="${loop.index}" ${('', 'selected="selected"')[selected_root == str(loop.index)]}>${loop.index}</option>
                        % endfor
                        </select>
                    </form>
                </label>
            % endif
            % if settings.HOME_LAYOUT != 'poster':
                <span class="show-option">
                    <button type="button" class="resetsorting btn btn-inline">${_('Clear Filter(s)')}</button>
                </span>
                <span class="show-option">
                    <button id="popover" type="button" class="btn btn-inline">${_('Select Columns')} <b class="caret"></b></button>
                </span>
            % endif
            <label>
                <span class="show-option">${_('Layout')}:</span>
                <select id="layout" class="form-control form-control-inline input-sm" title="Layout">
                    <option value="${scRoot}/setHomeLayout/?layout=poster" ${('', 'selected="selected"')[settings.HOME_LAYOUT == 'poster']}>${_('Poster')}</option>
                    <option value="${scRoot}/setHomeLayout/?layout=small" ${('', 'selected="selected"')[settings.HOME_LAYOUT == 'small']}>${_('Small Poster')}</option>
                    <option value="${scRoot}/setHomeLayout/?layout=banner" ${('', 'selected="selected"')[settings.HOME_LAYOUT == 'banner']}>${_('Banner')}</option>
                    <option value="${scRoot}/setHomeLayout/?layout=simple" ${('', 'selected="selected"')[settings.HOME_LAYOUT == 'simple']}>${_('Simple')}</option>
                </select>
            </label>
            % if settings.HOME_LAYOUT == 'poster':
                <label>
                    <span class="show-option">${_('Sort By')}:</span>
                    <select id="postersort" class="form-control form-control-inline input-sm" title="Poster Sort">
                        <option value="name" data-sort="${scRoot}/setPosterSortBy/?sort=name" ${('', 'selected="selected"')[settings.POSTER_SORTBY == 'name']}>${_('Name')}</option>
                        <option value="date" data-sort="${scRoot}/setPosterSortBy/?sort=date" ${('', 'selected="selected"')[settings.POSTER_SORTBY == 'date']}>${_('Next Episode')}</option>
                        <option value="network" data-sort="${scRoot}/setPosterSortBy/?sort=network" ${('', 'selected="selected"')[settings.POSTER_SORTBY == 'network']}>${_('Network')}</option>
                        <option value="progress" data-sort="${scRoot}/setPosterSortBy/?sort=progress" ${('', 'selected="selected"')[settings.POSTER_SORTBY == 'progress']}>${_('Progress')}</option>
                        <option value="status" data-sort="${scRoot}/setPosterSortBy/?sort=status" ${('', 'selected="selected"')[settings.POSTER_SORTBY == 'status']}>${_('Status')}</option>
                    </select>
                </label>

                <label>
                    <span class="show-option">${_('Direction')}:</span>
                    <select id="postersortdirection" class="form-control form-control-inline input-sm" title="Sort">
                        <option value="true" data-sort="${scRoot}/setPosterSortDir/?direction=1" ${('', 'selected="selected"')[settings.POSTER_SORTDIR == 1]}>${_('Ascending')} </option>
                        <option value="false" data-sort="${scRoot}/setPosterSortDir/?direction=0" ${('', 'selected="selected"')[settings.POSTER_SORTDIR == 0]}>${_('Descending')}</option>
                    </select>
                </label>
                <label>
                    <span class="show-option">${_('Poster Size')}:</span>
                    <span style="width: 100px; display: inline-block; margin-left: 7px;" id="posterSizeSlider"></span>
                </label>
            % endif
        </div>
    </div>
</div>
