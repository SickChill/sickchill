<%inherit file="../layouts/main.mako"/>
<%block name="css">
</%block>
<%block name="scripts">
</%block>
<%block name="content">
    <div id="movie-list">
        % for movie in movies:
            <div class="show-container">${movie.name}</div>
        % endfor
    </div>
</%block>
