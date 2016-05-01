<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="scripts">
	<script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
	<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
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
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
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
                <div class="row">
                    <div class="col-lg-4 col-md-4 col-sm-6 col-xs-12">
	                    <span>Sort By:</span>
	                    <select id="showsort" class="form-control form-control-inline input-sm" title="Show Sort">
		                    <option value="name">${_('Name')}</option>
		                    <option value="original" selected="selected">${_('Original')}</option>
		                    <option value="votes">${_('Votes')}</option>
		                    <option value="rating">% ${_('Rating')}</option>
		                    <option value="rating_votes">% ${_('Rating > Votes')}</option>
	                    </select>
                    </div>
	                <div class="col-lg-4 col-md-3 col-sm-6 col-xs-12">
	                    <span>${_('Sort Order')}:</span>
	                    <select id="showsortdirection" class="form-control form-control-inline input-sm" title="Show Sort Direction">
		                    <option value="asc" selected="selected">${_('Asc')}</option>
		                    <option value="desc">${_('Desc')}</option>
	                    </select>
                    </div>
	                <div class="col-lg-4 col-md-5 col-sm-6 col-xs-12">
	                    <span>${_('Select Trakt List')}:</span>
	                    <select id="traktlistselection" class="form-control form-control-inline input-sm" title="Trakt List Selection">
		                    <option value="anticipated" ${' selected="selected"' if traktList == "anticipated" else ''}>${_('Most Anticipated')}</option>
		                    <option value="newshow" ${' selected="selected"' if traktList == "newshow" else ''}>${_('New Shows')}</option>
		                    <option value="newseason" ${' selected="selected"' if traktList == "newseason" else ''}>${_('Season Premieres')}</option>
		                    <option value="trending" ${' selected="selected"' if traktList == "trending" else ''}>${_('Trending')}</option>
		                    <option value="popular" ${' selected="selected"' if traktList == "popular" else ''}>${_('Popular')}</option>
		                    <option value="watched" ${' selected="selected"' if traktList == "watched" else '' }>${_('Most Watched')}</option>
		                    <option value="played" ${' selected="selected"' if traktList == "played" else '' }>${_('Most Played')}</option>
		                    <option value="collected" ${' selected="selected"' if traktList == "collected" else ''}>${_('Most Collected')}</option>
                            % if sickbeard.TRAKT_ACCESS_TOKEN:
			                    <option value="recommended"  ${' selected="selected"' if traktList == "recommended" else ''}>${_('Recommended')}</option>
                            % endif
	                    </select>
                    </div>
                </div>
            </div>
            <div class="clearfix"></div>
            <div id="trendingShows"></div>
            % if traktList:
                <input type="hidden" name="traktList" id="traktList" value="${traktList}"/>
            % endif
        </div>
    </div>
</%block>
