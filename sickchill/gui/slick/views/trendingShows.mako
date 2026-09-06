<%inherit file="/layouts/main.mako" />
<%!
    from sickchill import settings
    from sickchill.oldbeard.helpers import anon_url
    from urllib.parse import quote_plus
%>
<%block name="metas">
    <meta data-var="settings.SORT_ARTICLE" data-content="${settings.SORT_ARTICLE}">
    <meta data-var="settings.GRAMMAR_ARTICLES" data-content="${settings.GRAMMAR_ARTICLES}">
</%block>
<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/trendingShows.js')}"></script>
</%block>
<%block name="content">
    <div id="container">
        % if not trending_shows:
            <div class="trakt_show" style="width:100%; margin-top:20px; text-align:left; padding:1em;">
                % if list_status and list_status.get("code") not in (None, "ok"):
                    <div class="alert alert-warning">
                        % if list_status.get("title"):
                            <strong>${list_status["title"]}</strong>
                        % endif
                        % if list_status.get("message"):
                            <p>${list_status["message"]}</p>
                        % endif
                        % if list_status.get("settings_url") and list_status.get("settings_label"):
                            <p>
                                <a class="btn btn-primary" href="${list_status['settings_url']}">
                                    ${list_status["settings_label"]}
                                </a>
                            </p>
                        % endif
                    </div>
                % else:
                    <p class="red-text">${_('No shows returned for this list.')}</p>
                % endif
            </div>
        % elif discovery_source == "trakt":
            % for cur_show in trending_shows:
                <%
                    show = cur_show.get("show") or cur_show
                    ids = show.get("ids") or {}
                    title = show.get("title") or ""
                    rating = show.get("rating") or 0
                    votes = show.get("votes") or 0
                    tvdb_id = ids.get("tvdb")
                    slug = ids.get("slug") or ""
                    show_url = "http://www.trakt.tv/shows/%s" % slug if slug else "#"
                    image_path = cur_show.get("image_path") or ""
                    indexer_id = cur_show.get("indexer_id") or ""
                    rating_pct = int(round(float(rating) * 10)) if rating else 0
                %>
                <div class="trakt_show" data-name="${title | h}"
                     data-rating="${rating_pct | h}" data-votes="${votes | h}"
                     data-source="trakt">
                    <div class="traktContainer">
                        <div class="trakt-image">
                            <a class="trakt-image" href="${anon_url(show_url)}" target="_blank" rel="noreferrer">
                                <img alt="" class="trakt-image" src=""
                                     data-src-indexer-id="${indexer_id | h}"
                                     data-src-cache="${static_url('cache/' + image_path, include_version=True) if image_path else static_url('images/poster.png')}"
                                     height="273px" width="186px" />
                            </a>
                        </div>

                        <div class="show-title">
                            % if title:
                                ${title}
                            % else:
                                <span>&nbsp;</span>
                            % endif
                        </div>

                        <div class="clearfix">
                            % if rating:
                                <p>${rating_pct}% <span class="displayshow-icon-heart"></span></p>
                            % endif
                            % if votes:
                                <i>${votes} ${_('votes')}</i>
                            % endif
                            <div class="traktShowTitleIcons">
                                % if cur_show.get("already_added"):
                                    <span class="btn btn-xs disabled">${_('In Library')}</span>
                                % elif tvdb_id:
                                    <a href="${scRoot}/addShows/addShowByID?indexer_id=${tvdb_id}&amp;show_name=${quote_plus(title)}"
                                       class="btn btn-xs">${_('Add Show')}</a>
                                    % if black_list:
                                        <a href="${scRoot}/addShows/addShowToBlacklist?indexer_id=${tvdb_id}"
                                           class="btn btn-xs">${_('Remove Show')}</a>
                                    % endif
                                % else:
                                    <a href="${scRoot}/addShows/newShow/?search_string=${quote_plus(title)}&amp;exact=1"
                                       class="btn btn-xs">${_('Search / Add')}</a>
                                % endif
                            </div>
                        </div>
                    </div>
                </div>
            % endfor
        % else:
            % for cur_show in trending_shows:
                <%
                    title = cur_show.get("title") or ""
                    rating = cur_show.get("rating") or 0
                    votes = cur_show.get("votes") or 0
                    poster = cur_show.get("poster_url") or ""
                    detail = cur_show.get("detail_url") or "#"
                    year = cur_show.get("year")
                    airdate = cur_show.get("airdate") or ""
                    tmdb_id = cur_show.get("tmdb_id")
                    tvdb_id = cur_show.get("tvdb_id")
                    already = cur_show.get("already_added")
                    source = cur_show.get("source") or ""
                    language = cur_show.get("language") or ""
                    # rating display: TMDB is 0–10; TVMaze average is 0–10
                    rating_pct = int(round(float(rating) * 10)) if rating else 0
                %>
                <div class="trakt_show" data-name="${title | h}"
                     data-rating="${rating_pct | h}" data-votes="${votes | h}"
                     data-airdate="${airdate | h}" data-tvdb-id="${(tvdb_id or '') | h}"
                     data-language="${language | h}" data-source="${source | h}">
                    <div class="traktContainer">
                        <div class="trakt-image">
                            <a class="trakt-image" href="${anon_url(detail)}" target="_blank" rel="noreferrer">
                                % if poster:
                                    <img alt="" class="trakt-image" src="${poster}" height="273px" width="186px" />
                                % else:
                                    <img alt="" class="trakt-image" src="${static_url('images/poster.png')}" height="273px" width="186px" />
                                % endif
                            </a>
                        </div>

                        <div class="show-title ${('has-tvdb' if tvdb_id else 'no-tvdb') if source == 'tvmaze' else ''}">
                            % if title:
                                ${title}${' ({})'.format(year) if year else ''}
                            % else:
                                <span>&nbsp;</span>
                            % endif
                            % if source == "tvmaze" and airdate:
                                <br/><small>${_('Airdate')}: ${airdate}</small>
                            % endif
                        </div>

                        <div class="clearfix">
                            % if rating:
                                <p>${rating_pct}% <span class="displayshow-icon-heart"></span></p>
                            % endif
                            % if votes:
                                <i>${votes} ${_('votes')}</i>
                            % endif
                            <div class="traktShowTitleIcons">
                                % if already:
                                    <span class="btn btn-xs disabled">${_('In Library')}</span>
                                % elif source == "tmdb" and tmdb_id:
                                    <a href="${scRoot}/addShows/addShowFromTMDB?tmdb_id=${tmdb_id}&amp;show_name=${quote_plus(title)}&amp;year=${year or ''}"
                                       class="btn btn-xs">${_('Add Show')}</a>
                                % elif tvdb_id:
                                    <a href="${scRoot}/addShows/addShowByID?indexer_id=${tvdb_id}&amp;show_name=${quote_plus(title)}"
                                       class="btn btn-xs">${_('Add Show')}</a>
                                % else:
                                    <a href="${scRoot}/addShows/newShow/?search_string=${quote_plus(title)}&amp;exact=1"
                                       class="btn btn-xs">${_('Search / Add')}</a>
                                % endif
                            </div>
                        </div>
                    </div>
                </div>
            % endfor
        % endif
    </div>
</%block>
