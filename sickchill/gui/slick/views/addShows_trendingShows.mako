<%inherit file="/layouts/main.mako" />
<%!
    from sickchill import settings
%>
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
            <div class="col-md-12 text-center">
                <label for="showsort">
                    <span>Sort By:</span>
                </label>

                <select id="showsort" class="form-control form-control-inline input-sm" title="Show Sort">
                    <option value="name">${_('Name')}</option>
                    <option value="original" selected>${_('Original')}</option>
                    <option value="votes">${_('Votes')}</option>
                    <option value="rating">% ${_('Rating')}</option>
                    <option value="rating_votes">% ${_('Rating > Votes')}</option>
                </select>
                <label for="showsortdirection">
                    <span>${_('Sort Order')}:</span>
                </label>

                <select id="showsortdirection" class="form-control form-control-inline input-sm" title="Show Sort Direction">
                    <option value="asc" selected>${_('Asc')}</option>
                    <option value="desc">${_('Desc')}</option>
                </select>
                <label for="traktlistselection">
                    <span>${_('Select Trakt List')}:</span>
                </label>

                <select id="traktlistselection" class="form-control form-control-inline input-sm" title="Trakt List Selection">
                    % for trakt_option in trakt_options:
                        <option value="${trakt_option}" ${selected(traktList == trakt_option)}>${trakt_option}</option>
                    % endfor
                </select>
            </div>
            <div class="clearfix"></div>
            <div id="trendingShows"></div>
            <input type="hidden" name="traktList" id="traktList" value="${traktList}" />
        </div>
    </div>
</%block>
