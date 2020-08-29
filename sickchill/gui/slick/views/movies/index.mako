<%inherit file="../layouts/main.mako"/>
<%block name="css">
</%block>
<%block name="scripts">
</%block>
<%block name="content">
    <div id="movie-list">
        % for movie in movies:
        <div class="poster-container col-md-3">
            <div class="show-container">
                <div class="show-image">
                    <a href="${reverse_url('movies-details', 'details', movie.slug)}">
                        <img alt="" class="show-image" src="${static_url("images/poster.png")}" />
                    </a>
                </div>

                <div class="show-information">
                    <div class="show-title">
                        ${movie.name}
                    </div>

                    <div class="show-date">
                        ${movie.date}
                    </div>

                    <div class="show-details">
                        <table class="show-details">
                        </table>
                    </div>
                </div>
            </div>
        </div>
        % endfor
    </div>
</%block>
