<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
%>
<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/blackwhite.js')}"></script>
</%block>
<%block name="content">
    <div id="tabs">
        <div class="row">
            <div class="col-md-12">
                % if not header is UNDEFINED:
                    <h1 class="header">${header}</h1>
                % else:
                    <h1 class="title">${title}</h1>
                % endif
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <ul>
                    <li><a href="#tabs-1">${_('Manage Directories')}</a></li>
                    <li><a href="#tabs-2">${_('Customize Options')}</a></li>
                </ul>
                <div id="tabs-1" class="existingtabs">
                        <%include file="/inc_rootDirs.mako"/>
                </div>
                <div id="tabs-2" class="existingtabs">
                        <%include file="/inc_addShowOptions.mako"/>
                </div>
            </div>
        </div>
        <br>
        <div class="row">
            <div class="col-md-12">
                <label>
                    <span>Sort By:</span>
                    <select id="showsort" class="form-control form-control-inline input-sm" title="Show Sort">
                        <option value="name">${_('Name')}</option>
                        <option value="original" selected="selected">${_('Original')}</option>
                        <option value="votes">${_('Votes')}</option>
                        <option value="rating">% ${_('Rating')}</option>
                        <option value="rating_votes">% ${_('Rating > Votes')}</option>
                    </select>
                    &nbsp;
                </label>
                <label>
                    <span>${_('Sort Order')}:</span>
                    <select id="showsortdirection" class="form-control form-control-inline input-sm" title="Show Sort Direction">
                        <option value="asc" selected="selected">${_('Asc')}</option>
                        <option value="desc">${_('Desc')}</option>
                    </select>
                    &nbsp;
                </label>
                <label>
                    <span>${_('Select Trakt List')}:</span>
                    <select id="traktlistselection" class="form-control form-control-inline input-sm" title="Trakt List Selection">
                        <option value="anticipated" ${('', ' selected="selected"')[traktList == "anticipated"]}>${_('Most Anticipated')}</option>
                        <option value="newshow" ${('', ' selected="selected"')[traktList == "newshow"]}>${_('New Shows')}</option>
                        <option value="newseason" ${('', ' selected="selected"')[traktList == "newseason"]}>${_('Season Premieres')}</option>
                        <option value="trending" ${('', ' selected="selected"')[traktList == "trending"]}>${_('Trending')}</option>
                        <option value="popular" ${('', ' selected="selected"')[traktList == "popular"]}>${_('Popular')}</option>
                        <option value="watched" ${('', ' selected="selected"')[traktList == "watched"]}>${_('Most Watched')}</option>
                        <option value="played" ${('', ' selected="selected"')[traktList == "played"]}>${_('Most Played')}</option>
                        <option value="collected" ${('', ' selected="selected"')[traktList == "collected"]}>${_('Most Collected')}</option>
                        % if settings.TRAKT_ACCESS_TOKEN:
                            <option value="recommended"  ${('', ' selected="selected"')[traktList == "recommended"]}>${_('Recommended')}</option>
                        % endif
                    </select>
                    &nbsp;
                </label>
            </div>
            <div class="clearfix"></div>
            <div id="trendingShows"></div>
            % if traktList:
                <input type="hidden" name="traktList" id="traktList" value="${traktList}"/>
            % endif
        </div>
    </div>
</%block>
