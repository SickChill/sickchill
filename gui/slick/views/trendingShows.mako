<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>
<%block name="metas">
    <meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
</%block>
<%block name="content">
    <div id="container">
        % if not trending_shows:
            <div class="trakt_show" style="width:100%; margin-top:20px">
                <p class="red-text">${_('Trakt API did not return any results, please check your config.')}
            </div>
        % else:
            % for cur_show in trending_shows:
                <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show['show']['ids']['slug'] %>

                % if 'poster' in cur_show['show']['images'] and cur_show['show']['images']['poster']['thumb']:
                    <% poster_url = cur_show['show']['images']['poster']['thumb'] %>
                % else:
                    <% poster_url = 'http://www.trakt.tv/assets/placeholders/thumb/poster-2d5709c1b640929ca1ab60137044b152.png' %>
                % endif

                <div class="trakt_show" data-name="${cur_show['show']['title']}"
                     data-rating="${cur_show['show']['rating']}" data-votes="${cur_show['show']['votes']}">
                    <div class="traktContainer">
                        <div class="trakt-image">
                            <a class="trakt-image" href="${anon_url(show_url)}" target="_blank">
                                <img alt="" class="trakt-image" src="${poster_url}" height="273px" width="186px"/>
                            </a>
                        </div>

                        <div class="show-title">
                            ${(cur_show['show']['title'], '<span>&nbsp;</span>')['' == cur_show['show']['title']]}
                        </div>

                        <div class="clearfix">
                            <p>${int(cur_show['show']['rating']*10)}% <span class="displayshow-icon-heart"></p>
                            <i>${cur_show['show']['votes']} ${_('votes')}</i>
                            <div class="traktShowTitleIcons">
                                <a href="${srRoot}/addShows/addShowByID?indexer_id=${cur_show['show']['ids']['tvdb']}&amp;show_name=${cur_show['show']['title'] | u}"
                                   class="btn btn-xs" data-no-redirect>${_('Add Show')}</a>
                                % if blacklist:
                                    <a href="${srRoot}/addShows/addShowToBlacklist?indexer_id=${cur_show['show']['ids']['tvdb'] or cur_show['show']['ids']['tvrage']}"
                                       class="btn btn-xs">${_('Remove Show')}</a>
                                % endif
                            </div>
                        </div>
                    </div>
                </div>
            % endfor
        % endif
    </div>
</%block>
