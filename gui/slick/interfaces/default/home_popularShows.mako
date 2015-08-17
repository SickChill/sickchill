<% from sickbeard.helpers import anon_url %>

<%include file="/inc_top.mako"/>

% if not popular_shows:
    <h3>Fetching of IMDB Data failed. Are you online?</h3>

% else:
    % for cur_result in popular_shows:
        <div class="popularShow">
            <div class="left">
                <img class="coverImage" src="${cur_result['image_url_large']}" />
            </div>
            <div class="right">
                <h3>${cur_result['name']}</h3>

                % if 'rating' in cur_result and cur_result['rating']:
                    <span class="rating">${cur_result['rating']}/10 (${cur_result['votes']})</span>
                % endif

                <p>${cur_result['outline']}<span class="year"> - Released ${cur_result['year']}<span></p>
                <span class="imdb_url"><a href="${anon_url(cur_result['imdb_url'])}">View on IMDB</a></span>&nbsp;&nbsp;|&nbsp;&nbsp;
                <span class="imdb_sickrage_search"><a href="/home/addShows/newShow/?search_string=${cur_result['name']}">
                    Add Show</a></span>

            </div>
            <br style="clear:both" />

        </div>
    % endfor
% endif


<%include file="/inc_bottom.mako"/>
