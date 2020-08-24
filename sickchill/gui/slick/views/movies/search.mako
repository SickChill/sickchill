<%inherit file="../layouts/config.mako"/>
<%block name="css">
</%block>
<%block name="scripts">
    <script xmlns="http://www.w3.org/1999/html">
        $('#config-components').tabs();
    </script>
</%block>

<%block name="tabs">
    <li><a href="#tmdb">Search TMDB</a></li>
    <li><a href="#tmdb_popular">Popular on TMDB</a></li>
    <li><a href="#imdb">Search iMDB</a></li>
    <li><a href="#imdb_popular">Popular on iMDB</a></li>
</%block>

<%block name="saveButton">
</%block>

<%block name="pages">
    <div id="config-components">
        <!-- /component-group1 //-->
        <div id="tmdb" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Search TMDB')}</h3>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <form method="post" class="form-horizontal">
                        <fieldset class="component-group-list">
                            <div class="field-pair row">
                                <div class="col-md-12">
                                    <div class="row">
                                        <label for="query" class="col-md-2 control-label">
                                            ${_('Enter a title or id')}:
                                        </label>
                                        <div class="col-md-10">
                                            <input type="text" name="query" id="query" class="form-control input-sm input350" autocapitalize="off"  title="Search"/>
                                            <input class="btn btn-inline" type="button" value="Search" id="Search" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="Result" id="imdb-result"></div>
                        </fieldset>
                    </form>
                </div>
            </div>
        </div>
        <div id="tmdb_popular" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Popular on TMDB')}</h3>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    % for result in movies.popular_tmdb():
                        <form method="post" class="form-horizontal">
                            ${result}
                        </form>
                    % endfor

                </div>
            </div>
        </div>
        <div id="imdb" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Search iMDB')}</h3>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <form method="post" class="form-horizontal">
                        <fieldset class="component-group-list">
                            <div class="field-pair row">
                                <div class="col-md-12">
                                    <div class="row">
                                        <label for="query" class="col-md-2 control-label">
                                            ${_('Enter a title or id')}:
                                        </label>
                                        <div class="col-md-10">
                                            <input type="text" name="query" id="query" class="form-control input-sm input350" autocapitalize="off"  title="Search"/>
                                            <input class="btn btn-inline" type="button" value="Search" id="Search" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="Result" id="imdb-result"></div>
                        </fieldset>
                    </form>
                </div>
            </div>
        </div>
        <div id="imdb_popular" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <h3>${_('Popular on iMDB')}</h3>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    % for result in movies.popular_imdb():
                        <div class="poster-container">
                            <div class="well well-sm">
                            <img src="${result['image']['url']}" class="tvshowImg" alt="${_('Poster for')} ${result['title']} - ${result['year']}"/>
                            <form method="post" class="form-horizontal">
                                <input type="hidden" name="imdb" value="${result['id'].split('/')[2:-1][0]}">
                                <button type="submit" class="btn btn-primary">Add</button>
                            </form>
                            </div>
                        </div>
                    % endfor

                </div>
            </div>
        </div>
    </div>

</%block>
