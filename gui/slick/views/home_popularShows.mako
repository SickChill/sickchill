<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard.helpers import anon_url
%>
<%block name="content">
<h2>Popular Shows</h2>
<br />

% if not popular_shows:
    <h3>Fetching of IMDB Data failed. Are you online?</h3>

    <strong>Exception:</strong>
    <p>${imdb_exception}</p>

% else:
    % for cur_result in popular_shows:
        <div class="popularShow">
            <div class="left">
                <img class="coverImage" src="${sbRoot}/cache/${cur_result['image_path']}" />
            </div>
            <div class="right">
                <h3>${cur_result['name']}</h3>

                % if 'rating' in cur_result and cur_result['rating']:
                    <span class="rating">${cur_result['rating']}/10 (${cur_result['votes']})</span>
                % endif

                <p>${cur_result['outline']}<span class="year"> - Released ${cur_result['year']}<span></p>
                <span class="imdb_url"><a href="${anon_url(cur_result['imdb_url'])}">View on IMDB</a></span>&nbsp;&nbsp;|&nbsp;&nbsp;
                <span class="imdb_sickrage_search"><a href="${sbRoot}/home/addShows/newShow/?search_string=${cur_result['name']}">
                    Add Show</a></span>

            </div>
            <br style="clear:both" />

        </div>
    % endfor
% endif
</%block>
