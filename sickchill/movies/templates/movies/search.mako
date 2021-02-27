<%inherit file="../layouts/config.mako"/>
<%block name="css">
</%block>
<%block name="scripts">
    <script xmlns="http://www.w3.org/1999/html">
        $('#config-components').tabs();
    </script>
</%block>

<%block name="tabs">
    <li><a href="#movie-search">Search</a></li>
    <li><a href="#tmdb-popular">Popular on TMDB</a></li>
    <li><a href="#imdb-popular">Popular on iMDB</a></li>
</%block>

<%block name="saveButton">
</%block>

<%block name="pages">
    <div id="config-components">
        <!-- /component-group1 //-->
        <div id="movie-search" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Search')}</h3>
                    <form method="post">
                        <div class="form-group">
                            <label for="query">${_('Query')}</label>
                            <input type="text" name="query" id="query" class="form-control input-sm input350" aria-describedby="queryHelp" autocapitalize="off" title="${_('Query')}" value="${query}"/>
                            <small id="queryHelp" class="form-text text-muted">${_('This can be a search string or a movie id from tmdb or imdb')}</small>
                        </div>
                        <div class="form-group">
                            <label for="year">${'Year'}</label>
                            <input type="text" name="year" id="year" class="form-control input-sm input75" aria-describedby="yearHelp" title="${'Year'}" value="${year}">
                            <small id="yearHelp" class="form-text text-muted">${_('This can be blank or the year for the movie')}</small>
                        </div>
                        <div class="form-group">
                            <label for="language">${'Language'}</label>
                            <input disabled type="text" name="language" id="language" class="form-control input-sm input75" aria-describedby="languageHelp" title="${'Language'}" value="${language}">
                            <small id="languageHelp" class="form-text text-muted">${_('This field is not yet implemented')}</small>
                        </div>
                        <div class="form-group">
                            <label for="language">${'Adult'}</label>
                            <input type="checkbox" name="adult" id="adult"aria-describedby="adultHelp" title="${'Adult'}" value="${adult}">
                            <small id="adultHelp" class="form-text text-muted">${_('Check if you want to include adult movies in the results')}</small>
                        </div>
                        <div class="form-group">
                            <button type="submit" class="btn btn-primary">Submit</button>
                        </div>
                    </form>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    % for result in search_results:
                        <div class="poster-container">
                            <div class="movie-container">
                                <div class="movie-image">
                                    <img
                                            src="${static_url("images/poster.png")}"
                                            data-src="${f'https://image.tmdb.org/t/p/w300_and_h450_bestv2{result["poster_path"]}'}"
                                            class="tvshowImg" alt="${_('Poster for')} ${result['title']} - ${result['release_date']}"
                                            onerror="this.src='${static_url("images/poster.png")}'"
                                    />
                                </div>
                                <div class="movie-information">
                                    <div class="movie-title">
                                        ${result['title'][0:34]}
                                    </div>

                                    <div class="movie-date">
                                        ${result['release_date']}
                                    </div>

                                    <div class="movie-details">
                                        <form method="post" action="${reverse_url('movies-add', 'add')}" class="form-horizontal pull-right">
                                            <input type="hidden" name="tmdb" value="${result['id']}">
                                            <button type="submit" class="btn btn-primary">Add</button>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endfor
                </div>
            </div>
        </div>
        <div id="tmdb-popular" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Popular on TMDB')}</h3>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    % for result in movies.popular_tmdb():
                        ## {'popularity': 614.082, 'vote_count': 869, 'video': False, 'poster_path': '/TnOeov4w0sTtV2gqICqIxVi74V.jpg', 'id': 605116, 'adult': False, 'backdrop_path': '/qVygtf2vU15L2yKS4Ke44U4oMdD.jpg', 'original_language': 'en', 'original_title': 'Project Power', 'genre_ids': [28, 80, 878], 'title': 'Project Power', 'vote_average': 6.7, 'overview': 'An ex-soldier, a teen and a cop collide in New Orleans as they hunt for the source behind a dangerous new pill that grants users temporary superpowers.', 'release_date': '2020-08-14'}
                        <div class="poster-container">
                            <div class="movie-container">
                                <div class="movie-image">
                                    <img
                                            src="${static_url("images/poster.png")}"
                                            data-src="${f'https://image.tmdb.org/t/p/w300_and_h450_bestv2{result["poster_path"]}' if result["poster_path"] else static_url("images/poster.png")}"
                                            class="tvshowImg" alt="${_('Poster for')} ${result['title']} - ${result['release_date']}"
                                            onerror="this.src='${static_url("images/poster.png")}'"
                                    />
                                </div>
                                <div class="movie-information">
                                    <div class="movie-title">
                                        ${result['title'][0:34]}
                                    </div>

                                    <div class="movie-date">
                                        ${result['release_date']}
                                    </div>
                                    <div class="movie-details">
                                        <form method="post" action="${reverse_url('movies-add', 'add')}" class="form-horizontal pull-right">
                                            <input type="hidden" name="tmdb" value="${result['id']}">
                                            <button type="submit" class="btn btn-primary">Add</button>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endfor
                </div>
            </div>
        </div>
        <div id="imdb-popular" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Popular on iMDB')}</h3>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    % for result in movies.popular_imdb():
                        <div class="poster-container">
                            <div class="movie-container">
                                <div class="movie-image">
                                    <img
                                            src="${static_url("images/poster.png")}" data-src="${result.get_fullsizeURL() or static_url("images/poster.png")}"
                                            class="tvshowImg" alt="${_('Poster for')} ${result['title']} - ${result.get('year', 'TBD')}"
                                            onerror="this.src='${static_url("images/poster.png")}'"
                                    />
                                </div>
                                <div class="movie-information">
                                    <div class="movie-title">
                                        ${result['title'][0:34]}
                                    </div>

                                    <div class="movie-date">
                                        ${result.get('year', 'TBD')}
                                    </div>
                                    <div class="movie-details">
                                        <form method="post" action="${reverse_url('movies-add', 'add')}" class="form-horizontal pull-right">
                                            <input type="hidden" name="imdb" value="${result.getID()}">
                                            <button type="submit" class="btn btn-primary">Add</button>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endfor

                </div>
            </div>
        </div>
    </div>
</%block>
