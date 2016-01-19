<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard.helpers import anon_url
    import sickbeard
%>
<%block name="metas">
<meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="tabs">
    <span>Sort By:</span>
    <select id="showsort" class="form-control form-control-inline input-sm">
        <option value="name">Name</option>
        <option value="original" selected="selected">Original</option>
        <option value="votes">Votes</option>
        <option value="rating">% Rating</option>
        <option value="rating_votes">% Rating > Votes</option>
    </select>

    <span style="margin-left:12px">Sort Order:</span>
    <select id="showsortdirection" class="form-control form-control-inline input-sm">
        <option value="asc" selected="selected">Asc</option>
        <option value="desc">Desc</option>
    </select>
</div>

<% current_shows = [show.indexerid for show in sickbeard.showList if show.indexerid] %>

<br>
<div id="popularShows">
    <div id="container">
    % if not anime:
        <div class="trakt_show" style="width:100%; margin-top:20px">
            <p class="red-text">Fetching of AniDB Data failed. Are you online?
            <strong>Exception:</strong>
            <p>${imdb_exception}</p>
        </div>
    % else:
        % for cur_result in anime:

            % if cur_result.ratings:
                <% cur_rating = cur_result.ratings['temporary']['rating'] %>
                <% cur_votes = cur_result.ratings['temporary']['count'] %>
            % else:
                <% cur_rating = '0' %>
                <% cur_votes = '0' %>
            % endif
            
            <% show_title = cur_result.titles['x-jat'][0].title %>

            <div class="trakt_show" data-name="${show_title}" data-rating="${cur_rating}" data-votes="${cur_votes}">
                <div class="traktContainer">
                    <div class="trakt-image">
                        <a class="trakt-image" href="/" target="_blank">
                            <img alt="" class="trakt-image" src="http://img7.anidb.net/pics/anime/${cur_result.picture}" height="273px" width="186px" />
                        </a>
                    </div>

                    <div class="show-title">
                        ${show_title}
                    </div>

                    <div class="clearfix">
                        <p>${int(float(cur_rating)*10)}% <img src="${srRoot}/images/heart.png"></p>
                        <i>${cur_votes} votes</i>
                        <div class="traktShowTitleIcons">
                            <a href="${srRoot}/addShows/addShowByID?indexer_id=${cur_result.tvdbid}&amp;show_name=${show_title | u}&amp;indexer=TVDB" class="btn btn-xs" data-no-redirect>Add Show</a>
                        </div>
                    </div>
                </div>
            </div>
        % endfor
    % endif
    </div>
</div>
<br>
</%block>
