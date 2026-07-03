<%inherit file="/layouts/main.mako" />
<%!
    from sickchill.oldbeard.helpers import anon_url
    from sickchill import settings
%>

<%block name="metas">
    <meta data-var="settings.SORT_ARTICLE" data-content="${settings.SORT_ARTICLE}">
    <meta data-var="settings.GRAMMAR_ARTICLES" data-content="${settings.GRAMMAR_ARTICLES}">
</%block>

<%block name="content">
    <div class="col-md-12">
        <div class="row">
            <div class="col-lg-8 col-md-7 col-sm-7 col-xs-12 pull-right">
                <div class="pull-right">
                    <label>
                        <span>${_('Sort By')}:</span>
                        <select id="showsort" class="form-control form-control-inline input-sm">
                            <option value="name">${_('Name')}</option>
                            <option value="rank" selected>${_('Rank')}</option>
                        </select>
                    </label>
                </div>
            </div>
            <div class="col-lg-4 col-md-5 col-sm-5 col-xs-12">
                <h1 class="header">${header}</h1>
            </div>
        </div>

        <div class="row">
            <div id="popularShows">
                <div id="container">
                    % if not popular_shows:
                        <div class="col-md-12">
                            <p class="red-text">${_('Fetching of IMDB Data failed. Are you online?')}</p>
                        </div>
                    % else:
                        % for current_result in popular_shows:
                            <div class="traktContainer">
                                <div class="trakt-image">
                                    <a href="${anon_url(imdb_url(current_result))}" target="_blank">
                                        <img src="${current_result.get('image') or static_url('images/poster.png')}"
                                             class="trakt-image"
                                             alt="${current_result.get('name', '')}"
                                             onerror="this.src='${static_url('images/poster.png')}'" />
                                    </a>
                                </div>

                                <div class="show-title">
                                    ${current_result.get('name', 'Unknown')}
                                    % if current_result.get('year'):
                                        <br><small>(${current_result['year']})</small>
                                    % endif
                                </div>

                                <div class="traktShowTitleIcons">
                                    % if current_result.get('current_imdb_id'):
                                        <span class="btn btn-xs btn-default disabled">Already Added</span>
                                    % else:
                                        <a href="${scRoot}/addShows/addShowByID?indexer_id=${current_result['imdb_id']}&amp;show_name=${current_result['name'] | u}&amp;indexer=IMDB"
                                           class="btn btn-xs btn-success">
                                            ${_('Add Show')}
                                        </a>
                                    % endif
                                </div>
                            </div>
                        % endfor
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>
