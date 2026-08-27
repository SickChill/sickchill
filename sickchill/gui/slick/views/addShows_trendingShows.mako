<%inherit file="/layouts/main.mako" />
<%!
    from sickchill import settings
%>
<%block name="content">
    <div id="tabs">
        <div class="discovery-toolbar">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
            <div class="discovery-filters">
                <label for="showsort">
                    <span>${_('Sort By')}:</span>
                </label>
                <select id="showsort" class="form-control form-control-inline input-sm" title="${_('Show Sort')}">
                    <option value="name">${_('Name')}</option>
                    <option value="original" selected>${_('Original')}</option>
                    <option value="votes">${_('Votes')}</option>
                    <option value="rating">% ${_('Rating')}</option>
                    <option value="rating_votes">% ${_('Rating > Votes')}</option>
                </select>
                <label for="showsortdirection">
                    <span>${_('Sort Order')}:</span>
                </label>
                <select id="showsortdirection" class="form-control form-control-inline input-sm" title="${_('Show Sort Direction')}">
                    <option value="asc" selected>${_('Asc')}</option>
                    <option value="desc">${_('Desc')}</option>
                </select>
                <label for="traktlistselection">
                    <span>${_('Select List')}:</span>
                </label>
                <select id="traktlistselection" class="form-control form-control-inline input-sm" title="${_('Discovery List Selection')}">
                    % for option_key, option_label in list_options.items():
                        <option value="${option_key}" ${selected(list_key == option_key)}>${option_label}</option>
                    % endfor
                </select>
            </div>
        </div>
        <div id="premiereFilters" class="discovery-filters" style="margin-bottom: 0.75em;${'' if list_key == 'premieres' else ' display:none;'}">
            <label for="premiere-window">
                <span>${_('Premiere window')}:</span>
            </label>
            <select id="premiere-window" class="form-control form-control-inline input-sm" title="${_('Premiere window')}">
                <option value="14" selected>${_('Next 14 days')}</option>
                <option value="30">${_('Next 30 days')}</option>
                <option value="all">${_('All')}</option>
            </select>
            <label class="checkbox-inline" style="margin-left: 0.75em;">
                <input type="checkbox" id="premiere-has-tvdb" checked />
                ${_('Has TVDB id')}
            </label>
            <label for="premiere-language" style="margin-left: 0.75em;">
                <span>${_('Language')}:</span>
            </label>
            <select id="premiere-language" class="form-control form-control-inline input-sm" title="${_('Language')}">
                <option value="english" selected>${_('English')}</option>
                <option value="all">${_('All')}</option>
            </select>
            <div class="help-block" style="margin-top: 0.5em;">
                ${_('TVMaze does not provide ratings for most upcoming premieres yet.')}
            </div>
        </div>
        <div id="trendingShows"></div>
        <input type="hidden" name="traktList" id="traktList" value="${list_key}" />
        <input type="hidden" name="tmdbList" id="tmdbList" value="${list_key}" />
    </div>
</%block>
