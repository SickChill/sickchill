<%inherit file="../layouts/main.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard import subtitles
    from sickchill.oldbeard.common import Quality, qualityPresets, statusStrings, Overview
    from sickchill.oldbeard.helpers import anon_url
    from sickchill.helper.common import pretty_file_size
%>

<%block name="css">
</%block>
<%block name="scripts">
</%block>
<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>
    <!-- Alert -->
    % if movie_message:
        <div class="row">
            <div class="col-md-12">
                <div class="alert alert-info">
                    ${movie_message}
                </div>
            </div>
        </div>
    % endif
    <div id="movies-details">
        <!-- Header -->
        <div class="row">
            <div class="col-md-12">
                <div class="poster-container">
                    <img class="tvshowImg" src="${static_url("images/poster.png")}" alt="${_('Poster for')} ${movie.name}"/>
                </div>
                <div class="info-container">
                    <div class="row">
                        % if movie.imdb_data:
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                % if 'rating' in movie.imdb_data and 'votes' in movie.imdb_data:
                                <% rating_tip = str(movie.imdb_data['rating']) + " / 10" + _('Stars') + "<br>" + str(movie.imdb_data['votes']) +  _('Votes') %>
                                    <span class="imdbstars" data-qtip-content="${rating_tip}">${movie.imdb_data['rating']}</span>
                                % endif

                                % if 'country_codes' in movie.imdb_data:
                                    % for country in movie.imdb_data['country_codes'].split('|'):
                                        <img src="${static_url('images/blank.png')}" class="country-flag flag-${country}" width="16" height="11" style="margin-left: 3px; vertical-align:middle;" />
                                    % endfor
                                % endif
                                % if movie.imdb_id:
                                    <span>
                                        % if movie.imdb_data.get('year'):
                                            (${movie.imdb_data['year']})
                                        % endif
                                        % if movie.imdb_data.get('runtime'):
                                            ${movie.imdb_data['runtimes']} ${_('minutes')}
                                        % endif
                                        </span>
                                    <a href="${anon_url('http://www.imdb.com/title/', movie.imdb_id)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="http://www.imdb.com/title/${movie.imdb_id}"><span class="displaymovie-icon-imdb"></span></a>
                                    <a href="${anon_url('https://trakt.tv/movies/', movie.imdb_id)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="https://trakt.tv/movies/${movie.imdb_id}"><span class="displaymovie-icon-trakt"></span></a>
                                % endif
                            </div>

                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                <ul class="tags">
                                    % if movie.imdb_data.get('genres'):
                                        % for imdbgenre in movie.imdb_data['genres'].replace('Sci-Fi','Science-Fiction').split('|'):
                                            <a href="${anon_url('http://www.imdb.com/search/title?count=100&title_type=tv_series&genres=', imdbgenre.lower())}" target="_blank" title="${_('View other popular {imdbgenre} movies on IMDB.').format(imdbgenre=_(imdbgenre))}"><li>${_(imdbgenre)}</li></a>
                                        % endfor
                                    % endif
                                </ul>
                            </div>
                        % endif
                        <div class="col-md-12">
                            <div id="summary">
                                <div class="col-lg-8 col-md-8 col-sm-8 col-xs-12">
                                    <table class="summaryTable pull-left">
                                        <tr>
                                            <td class="movieLegend">${_('Release Date')}: </td>
                                            <td>${movie.date}</td>
                                        </tr>
                                        <tr>
                                            <td class="movieLegend">${_('Movie Status')}: </td>
                                            <td>${_(movie.status)}</td>
                                        </tr>
                                        <tr>
                                            <td class="movieLegend">${_('Location')}: </td>
                                            <td>${movie.location}</td>
                                        </tr>
                                        % if movie.result:
                                            <tr>
                                                <td class="movieLegend">${_('Size')}:</td>
                                                <td>${pretty_file_size(movie.result.size)}</td>
                                            </tr>
                                        % endif


                                    </table>
                                </div>
                                <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12 pull-xs-left">
                                    <table class="pull-xs-left pull-md-right pull-sm-right pull-lg-right">
                                        <% info_flag = subtitles.code_from_code(movie.language) if movie.language else '' %>
                                        <tr>
                                            <td class="movieLegend">${_('Info Language')}:</td>
                                            <td><img src="${static_url('images/subtitles/flags/' + info_flag + '.png') }" width="16" height="11" alt="${movie.language}" title="${movie.language}" onError="this.onerror=null;this.src='${static_url('images/flags/unknown.png')}';"/></td>
                                        </tr>
                                        % if settings.USE_SUBTITLES:
                                            <tr>
                                                <td class="movieLegend">${_('Subtitles')}: </td>
                                                <td><span class="displaymovie-icon-${("disable", "enable")[bool(movie.subtitles)]}" title=${("N", "Y")[bool(movie.subtitles)]}></span></td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="movieLegend">${_('Paused')}: </td>
                                            <td><span class="displaymovie-icon-${("disable", "enable")[bool(movie.paused)]}" title=${("N", "Y")[bool(movie.paused)]}></span></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
