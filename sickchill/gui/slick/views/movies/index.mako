<%inherit file="../layouts/main.mako"/>
<%block name="css">
</%block>
<%block name="scripts">
</%block>
<%block name="content">
    <div id="movie-list">
        % for movie in movies:
        <div class="poster-container col-md-3">
            <div class="movie-container">
                <div class="movie-image">
                    <a href="${reverse_url('movies-details', 'details', movie.slug)}">
                        <img alt="" class="movie-image" src="${static_url("images/poster.png")}" data-src="${movie.imdb_data['base']['image']['url']}" />
                    </a>
                </div>

                <div class="movie-information">
                    <div class="movie-title">
                        ${movie.name}
                    </div>

                    <div class="movie-date">
                        ${movie.date}
                    </div>

                    <div class="movie-details">
                        <table class="movie-details">
                        </table>
                    </div>
                </div>
            </div>
        </div>
        % endfor
    </div>
</%block>
