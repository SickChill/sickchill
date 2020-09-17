<%inherit file="/layouts/main.mako"/>
<%!
    import timeago
    from datetime import datetime

    from sickchill.oldbeard.helpers import anon_url
    from sickchill import settings
%>
<%block name="metas">
    <meta data-var="settings.SORT_ARTICLE" data-content="${settings.SORT_ARTICLE}">
</%block>
<%block name="content">
    <div class="col-md-12">
        <div class="row">
            <div class="col-lg-8 col-md-7 col-sm-7 col-xs-12 pull-right">
                <div class="pull-right">
                    <label>
                        <span>${_('Sort By')}:</span>
                        <select id="showsort" class="form-control form-control-inline input-sm" title="Show Sort">
                            <option value="name">${_('Name')}</option>
                            <option value="original" selected="selected">${_('Original')}</option>
                            <option value="rank" selected="selected">${_('Rank')}</option>
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
                    </label>
                </div>
            </div>
            <div class="col-lg-4 col-md-5 col-sm-5 col-xs-12">
                % if not header is UNDEFINED:
                    <h1 class="header">${header}</h1>
                % else:
                    <h1 class="title">${title}</h1>
                % endif
            </div>
        </div>
        <div class="row">
            <% imdb_tt = {show.imdb_id for show in settings.showList if show.imdb_id} %>
            <div id="popularShows">
                <div id="container">
                    % if not popular_shows:
                        <div class="trakt_show" style="width:100%; margin-top:20px">
                            <p class="red-text">${_('Fetching of IMDB Data failed. Are you online?')}</p>
                            <strong>${_('Exception')}:</strong>
                            <p>${imdb_exception}</p>
                        </div>
                    % else:
                        % for current_result in popular_shows:
                            % if not current_result.getID():
                                <% continue %>
                            % endif

                            <% current_imdb_id = 'tt' + current_result.getID() %>
                            % if current_imdb_id in imdb_tt:
                                <% continue %>
                            % endif

                            <% current_result.setdefault('rating', '0.0') %>
                            <% current_result.setdefault('votes', '0') %>

                            <div class="trakt_show" data-name="${current_result['title']}" data-rating="${current_result['rating']}"
                                 data-votes="${str(current_result['votes']).replace(',', '')}" data-rank="${current_result['popular tv 100 rank']}">
                                <div class="traktContainer">
                                    <div class="trakt-image">
                                        <a class="trakt-image" href="${anon_url(imdb_url(current_result))}" target="_blank">
                                            <img alt="" class="trakt-image" src="${current_result.get_fullsizeURL() or static_url("images/poster.png")}"
                                                 height="273px" width="186px" onerror="this.src='${static_url("images/poster.png")}'"/>
                                        </a>
                                    </div>

                                    <div class="show-title">
                                        ${current_result.get('title','<span>&nbsp;</span>')} - (${current_result.get('year', 'TBD')})
                                    </div>

                                    <div class="clearfix">
                                        <p>${int(float(current_result['rating'])*10)}%&nbsp;<span class="displayshow-icon-heart"></span> <i>#${current_result['popular tv 100 rank']}</i></p>
                                        <i>${current_result['votes']}</i>

                                        <div class="traktShowTitleIcons">
                                            <a href="${scRoot}/addShows/addShowByID?indexer_id=${current_imdb_id}&amp;show_name=${current_result['title'] | u}&amp;indexer=IMDB"
                                               class="btn btn-xs" data-no-redirect>${_('Add Show')}</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        % endfor
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>
