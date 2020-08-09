<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill.oldbeard.helpers import anon_url
    from sickchill import settings
    from sickchill.oldbeard.filters import hide
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
            <div class="col-md-12 text-center">
                <form name="set_tvdb_key" class="form form-inline" method="post" action="">

                    <div class="form-group">
                        <label for="tvdb_user">${_('TVDB Username')}</label>
                        <input class="form-control" title="${_('TVDB Username')}" name="tvdb_user"
                               type="text" value="${settings.TVDB_USER or ''}" autocomplete="off"/>
                    </div>
                    <div class="form-group">
                        <label for="password">${_('TVDB User Key')}</label>
                        <input class="form-control" title="${_('TVDB User Key')}" name="tvdb_user_key"
                               type="password" value="${settings.TVDB_USER_KEY|hide}" autocomplete="off"/>
                    </div>
                    <div class="form-group">
                        <input class="btn btn-default pull-right" name="submit" type="submit" value="${_('Submit')}"/>
                    </div>
                </form>
            </div>
        </div>

        <div class="row">
            <div id="favoriteShows">
                <div id="container">
                    % if favorite_shows is None:
                        <div class="trakt_show" style="width:100%; margin-top:20px">
                            <p class="red-text">${_('Fetching of Favorites Data failed. Have you set your user name and key correctly?')}
                                <strong>${_('Exception')}:</strong>
                            <p>${favorites_exception}</p>
                        </div>
                    % elif not favorite_shows:
                        <div class="trakt_show text-center" style="width:100%; margin-top:20px">
                            ${_('No favorites found that are not already in your show list, or fetching failed. Make sure your username and user key are set correctly above if you feel this is an error')}
                        </div>
                    % else:
                        % for cur_result in favorite_shows:
                            <div class="trakt_show" data-name="${cur_result.seriesName}" data-rating="${cur_result.siteRating}"
                                 data-votes="${cur_result.siteRatingCount}">
                                <div class="traktContainer">
                                    <div class="trakt-image">
                                        <a class="trakt-image" href="${anon_url('https://thetvdb.com/series/' + cur_result.slug)}" target="_blank">
                                            <img alt="" class="trakt-image" src="${scRoot}/cache/images/favorites/${cur_result.id}"
                                                 height="273px" width="186px"/>
                                        </a>
                                    </div>

                                    <div class="show-title">
                                        ${(cur_result.seriesName, '<span>&nbsp;</span>')['' == cur_result.seriesName]}
                                    </div>

                                    <div class="clearfix">
                                        <p>${cur_result.siteRating*10}%&nbsp;<span class="displayshow-icon-heart"></span></p>
                                        <i>${cur_result.siteRatingCount}</i>
                                        <div class="traktShowTitleIcons">
                                            <a href="${scRoot}/addShows/addShowByID?indexer_id=${cur_result.id}&amp;show_name=${cur_result.seriesName | u}&amp;indexer=TVDB"
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
