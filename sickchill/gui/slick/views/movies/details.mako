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
    <script type="text/javascript" src="${static_url('js/lib/jquery.bookmarkscroll.js')}"></script>
    <script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/ratingTooltip.js')}"></script>
</%block>
<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>
    <div class="row">
        <div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" id="movie-title" data-moviename="${movie.name}">
            <h1 class="title" id="scene_exception_${movie.imdb_id}">${movie.name}</h1>
        </div>
    </div>
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
                    <img class="movieImg" src="${static_url("images/poster.png")}" data-src="${movie.imdb_data['base']['image']['url']}" alt="${_('Poster for')} ${movie.name}"/>
                </div>
                <div class="info-container">
                    <div class="row">
                        % if movie.imdb_data:
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                % if movie.imdb_rating and movie.imdb_votes:
                                    <span class="imdbstars" data-qtip-content="${f'{movie.imdb_rating} / 10 {_("Stars")}<br>{movie.imdb_votes} {_("Votes")}'}">${movie.imdb_rating}</span>
                                % endif
                                % if 'country_codes' in movie.imdb_data:
                                    % for country in movie.imdb_data['country_codes'].split('|'):
                                        <img src="${static_url('images/blank.png')}" class="country-flag flag-${country}" width="16" height="11" style="margin-left: 3px; vertical-align:middle;" />
                                    % endfor
                                % endif
                                <span>
                                    ${movie.year or _('Unknown')}
                                    ${movie.runtime or _('Unknown')} ${_('minutes')}
                                </span>
                                % if movie.imdb_id:
                                    <a href="${anon_url('http://www.imdb.com/title/', movie.imdb_id)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="http://www.imdb.com/title/${movie.imdb_id}"><span class="displaymovie-icon-imdb"></span></a>
                                    <a href="${anon_url('https://trakt.tv/movies/', movie.imdb_id)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="https://trakt.tv/movies/${movie.imdb_id}"><span class="displaymovie-icon-trakt"></span></a>
                                % endif
                            </div>
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                <ul class="tags">
                                    % for imdbgenre in movie.imdb_genres:
                                        <a href="${anon_url('http://www.imdb.com/search/title?count=100&title_type=tv_series&genres=', imdbgenre.pk.lower())}" target="_blank" title="${_('View other popular {imdbgenre} movies on IMDB.').format(imdbgenre=_(imdbgenre.pk))}"><li>${_(imdbgenre.pk)}</li></a>
                                    % endfor
                                </ul>
                            </div>
                        % endif
                        <div class="col-md-12">
                            <div id="summary">
                                <div class="col-lg-8 col-md-8 col-sm-8 col-xs-12">
                                    <table class="summaryTable pull-left">
                                        <tr>
                                            <td class="movieLegend">${_('Release Date')}: </td>
                                            <td>${movie.date or _('Unknown')}</td>
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
                                        <tr>
                                            <td class="movieLegend">${_('Plot')}</td>
                                            <td class="ep_summary" colspan="2">${movie.imdb_outline or _('N/A')}</td>
                                        </tr>

                                        <tr>
                                            <td class="movieLegend">${_('Summary')}</td>
                                            <td class="ep_summary" colspan="2">${movie.imdb_summary or _('N/A')}</td>
                                        </tr>
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
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(movie.subtitles)]}" title=${("N", "Y")[bool(movie.subtitles)]}></span></td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="movieLegend">${_('Paused')}: </td>
                                            <td><span class="displayshow-icon-${("disable", "enable")[bool(movie.paused)]}" title=${("N", "Y")[bool(movie.paused)]}></span></td>
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
