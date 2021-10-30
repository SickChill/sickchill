<%inherit file="/layouts/config.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard.helpers import anon_url
    from sickchill import indexer as show_indexer
%>
<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/blackwhite.js')}"></script>
</%block>

<%block name="tabs">
    <li><a href="#core-component-group1">${_('Add New Show')}</a></li>
</%block>

<%block name="saveButton"/>

<%block name="pages">
    <div id="core-component-group1" class="tab-pane active component-group">
        <div class="row">
            <div class="col-md-12">
                <form id="addShowForm" method="post" action="${scRoot}/addShows/addNewShow" accept-charset="utf-8" class="form form-inline">

                    <legend class="legendStep">#1 ${_('Search for a Show')}</legend>
                    <div class="row stepDiv">
                        <div class="col-md-12">
                            <input type="hidden" id="indexer_timeout" value="${settings.INDEXER_TIMEOUT}"/>

                            % if use_provided_info:
                                <label>${_('Show retrieved from existing metadata')}:
                                    <a href="${anon_url(show_indexer.show_url(provided_indexer), provided_indexer_id)}">${provided_indexer_name}</a>
                                </label>
                                <input type="hidden" id="indexerLang" name="indexerLang" value="en"/>
                                <input type="hidden" id="whichSeries" name="whichSeries" value="${provided_indexer_id}"/>
                                <input type="hidden" id="providedIndexer" name="providedIndexer" value="${provided_indexer}"/>
                                <input type="hidden" id="providedName" value="${provided_indexer_name}"/>
                            % else:
                                <div class="row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Show name')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <div class="input-group">
                                                    <input type="text" id="show-name" value="${default_show_name}"
                                                           placeholder="Show name" autofocus
                                                           autocapitalize="off"
                                                           class="form-control"
                                                    />
                                                    <span class="input-group-addon">
                                                        <input type="checkbox" id="exact-match">
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="field-pair row">
                                            <div class="col-md-12">
                                                <span><i>${_('Check the box for exact string search')}</i></span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Metadata language')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select name="indexerLang" id="indexerLangSelect"
                                                        class="form-control form-control-inline input-sm bfh-languages"
                                                        data-language="${settings.INDEXER_DEFAULT_LANGUAGE}"
                                                        data-available="${','.join(show_indexer.languages())}"></select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <span>${_('This will only affect the language of the retrieved metadata file contents and episode file names.')}</span>
                                                <br/>
                                                <span>${_('This <b>DOES NOT</b> allow SickChill to download non-english TV episodes!')}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Indexer')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <select name="providedIndexer" id="providedIndexer"
                                                class="form-control form-control-inline input-sm">
                                            <option value="0" ${('', 'selected="selected"')[provided_indexer == 0]}>${_('All Indexers')}</option>
                                            % for index, indexer in show_indexer:
                                                <option value="${index}" ${('', 'selected="selected"')[provided_indexer == index]}>
                                                    ${indexer.name}
                                                </option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">
                                            <input class="btn btn-inline" type="button" id="search-button" value="${_('Search')}"/>
                                        </span>
                                    </div>
                                </div>
                                <div id="searchResults"><br/></div>
                            % endif
                        </div>
                    </div>

                    <div class="next-steps" style="display: none;">
                        <legend class="legendStep">#3 ${_('Pick the Folder')}</legend>
                        <div class="row stepDiv">
                            <div class="col-lg-6 col-sm-12">
                                % if provided_show_dir:
                                    <p>${_('Pre-chosen Destination Folder')}:</p>
                                    <b style="font-size: 15px;">${provided_show_dir}</b>
                                    <br>
                                    <input type="hidden" id="fullShowPath" name="fullShowPath"
                                           value="${provided_show_dir}"/>
                                    <br/>
                                % else:
                                    <%include file="/inc_rootDirs.mako"/>
                                % endif
                            </div>
                        </div>

                        <legend class="legendStep">#4 ${_('Customize options')}</legend>
                        <div class="row stepDiv">
                            <div class="col-md-12">
                                    <%include file="/inc_addShowOptions.mako"/>
                            </div>
                        </div>

                        <legend class="legendStep">#5 ${_('Verify Your Input')}</legend>
                        <div class="row stepDiv">
                            <div class="col-md-12">
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Show name')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <span id="desc-show-name"></span>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Directory')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc desc-directory">
                                        <span id="desc-directory-name"></span>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Quality')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc desc-quality">
                                        <span id="desc-quality-name"></span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        % for curNextDir in other_shows:
                            <input type="hidden" name="other_shows" value="${curNextDir}"/>
                        % endfor
                        <input type="hidden" name="skipShow" id="skipShow"/>
                    </div>
                </form>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <input class="btn" type="button" id="addShowButton" value="${_('Add Show')}" disabled="disabled"/>
                % if provided_show_dir:
                    <input class="btn" type="button" id="skipShowButton" value="${_('Skip Show')}"/>
                % endif
            </div>
        </div>
    </div>
</%block>
