<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill.helpers import anon_url
    import sickchill
%>
<%block name="metas">
    <meta data-var="sickchill.SORT_ARTICLE" data-content="${sickchill.SORT_ARTICLE}">
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
            <% imdb_tt = {show.imdbid for show in sickchill.showList if show.imdbid} %>
            <div id="popularShows">
                <div id="container">
                    % if not popular_shows:
                        <div class="trakt_show" style="width:100%; margin-top:20px">
                            <p class="red-text">${_('Fetching of IMDB Data failed. Are you online?')}
                                <strong>${_('Exception')}:</strong>
                            <p>${imdb_exception}</p>
                        </div>
                    % else:
                        % for cur_result in popular_shows:
                            % if cur_result[b'imdb_tt'] in imdb_tt:
                                <% continue %>
                            % endif

                        % if 'rating' in cur_result and cur_result[b'rating']:
                            <% cur_rating = cur_result[b'rating'] %>
                            <% cur_votes = cur_result[b'votes'] %>
                        % else:
                            <% cur_rating = '0' %>
                            <% cur_votes = '0' %>
                        % endif

                            <div class="trakt_show" data-name="${cur_result[b'name']}" data-rating="${cur_rating}"
                                 data-votes="${cur_votes.replace(',', '')}">
                                <div class="traktContainer">
                                    <div class="trakt-image">
                                        <a class="trakt-image" href="${anon_url(cur_result[b'imdb_url'])}" target="_blank">
                                            <img alt="" class="trakt-image" src="${srRoot}/cache/${cur_result[b'image_path']}"
                                                 height="273px" width="186px"/>
                                        </a>
                                    </div>

                                    <div class="show-title">
                                        ${(cur_result[b'name'], '<span>&nbsp;</span>')['' == cur_result[b'name']]}
                                    </div>

                                    <div class="clearfix">
                                        <p>${int(float(cur_rating)*10)}%&nbsp;<span class="displayshow-icon-heart"></span></p>
                                        <i>${cur_votes}</i>
                                        <div class="traktShowTitleIcons">
                                            <a href="${srRoot}/addShows/addShowByID?indexer_id=${cur_result[b'imdb_tt']}&amp;show_name=${cur_result[b'name'] | u}&amp;indexer=IMDB"
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
