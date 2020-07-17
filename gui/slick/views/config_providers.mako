<%inherit file="/layouts/config.mako"/>
<%!
    import sickbeard
    from sickbeard.filters import hide
    from sickbeard.helpers import anon_url
    from sickchill.providers.media.GenericProvider import GenericProvider
%>

<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/configProviders.js')}"></script>
    <script type="text/javascript">
        $(document).ready(function() {
            $('#config-components').tabs();
            % if sickbeard.USE_NZBS:
                % for curNewznabProvider in sickbeard.newznabProviderList:
                    $(this).addNZBProvider(
                        '${curNewznabProvider.get_id()}',
                        '${curNewznabProvider.config('name')}',
                        '${curNewznabProvider.config('url')}',
                        '${curNewznabProvider.config('key')}',
                        '${curNewznabProvider.config('categories')}'
                    );
                % endfor
            % endif
            % if sickbeard.USE_TORRENTS:
                % for curTorrentRssProvider in sickbeard.torrentRssProviderList:
                    $(this).addTorrentRssProvider(
                        '${curTorrentRssProvider.get_id()}',
                        '${curTorrentRssProvider.config('name')}',
                        '${curTorrentRssProvider.config('url')}',
                        '${curTorrentRssProvider.config('cookies')}',
                        '${curTorrentRssProvider.config('title_tag')}'
                    );
                % endfor
            % endif
        });
    </script>
</%block>

<%block name="tabs">
    <li><a href="#provider-priorities">${_('Provider Priorities')}</a></li>
    <li><a href="#provider-options">${_('Provider Options')}</a></li>

    % if sickbeard.USE_NZBS:
        <li><a href="#custom-newznab">${_('Configure Custom Newznab Providers')}</a></li>
    % endif

    % if sickbeard.USE_TORRENTS:
        <li><a href="#custom-torrent">${_('Configure Custom Torrent Providers')}</a></li>
    % endif
</%block>

<%block name="pages">
    <form id="configForm" action="saveProviders" method="post">

        <div id="provider-priorities" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <h3>${_('Provider Priorities')}</h3>
                        <p>${_('Check off and drag the providers into the order you want them to be used.')}</p>
                        <p>${_('At least one provider is required but two are recommended.')}</p>

                        % if not sickbeard.USE_NZBS or not sickbeard.USE_TORRENTS:
                            <blockquote style="margin: 20px 0;">NZB/${_('Torrent and NZB providers can be toggled in ')}
                                <b><a href="/config/search">Search Settings</a></b></blockquote>
                        % else:
                            <br>
                        % endif

                        <div>
                            <p class="note"><span class="red-text">*</span> ${_('Provider does not support backlog or manual searches')}</p>
                            <p class="note"><span class="red-text">!</span> ${_('Provider does not support daily rss searches')}</p>
                        </div>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <ul id="provider_order_list">
                            % for curProvider in sickbeard.providers.sortedProviderList():
                            <%
                                if curProvider.provider_type == GenericProvider.NZB and not sickbeard.USE_NZBS:
                                    continue
                                elif curProvider.provider_type == GenericProvider.TORRENT and not sickbeard.USE_TORRENTS:
                                    continue

                                curName = curProvider.get_id()
                                if hasattr(curProvider, 'custom_url'):
                                    curURL = curProvider.custom_url or curProvider.url
                                else:
                                    curURL = curProvider.url
                            %>
                                <li class="ui-state-default ${('nzb-provider', 'torrent-provider')[curProvider.provider_type == GenericProvider.TORRENT]}" id="${curName}">
                                    <input type="checkbox" id="enable_${curName}" class="provider_enabler" ${('', 'checked="checked"')[curProvider.config('enabled')]}/>
                                    <a href="${anon_url(curURL)}" class="imgLink" rel="noreferrer"
                                       onclick="window.open(this.href, '_blank'); return false;">
                                        <img src="${static_url('images/providers/' + curProvider.image_name())}"
                                            alt="${curProvider.name}" title="${curProvider.name}" width="16"
                                            height="16" style="vertical-align:middle;"/>
                                    </a>
                                    <label for="enable_${curName}" style="vertical-align:middle;">${curProvider.name}</label>
                                    ${('<span class="red-text">*</span>', '')[curProvider.can_backlog]}
                                    ${('<span class="red-text">!</span>', '')[curProvider.can_daily]}
                                    <span class="ui-icon ui-icon-arrowthick-2-n-s pull-right" style="vertical-align:middle;"></span>
                                    <span class="ui-icon ${('ui-icon-locked','ui-icon-unlocked')[curProvider.config('public')]} pull-right" style="vertical-align:middle;"></span>
                                </li>
                            % endfor
                        </ul>
                        <input type="hidden" name="provider_order" id="provider_order" value="${" ".join([x.get_id(':'+str(int(x.config('enabled')))) for x in sickbeard.providers.sortedProviderList()])}" />
                    </fieldset>
                </div>
            </div>
        </div>

        <div id="provider-options" class="component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <h3>${_('Provider Options')}</h3>
                        <p>${_('Configure individual provider settings here.')}</p>
                        <p>${_('Check with provider\'s website on how to obtain an API key if needed.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">

                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Configure provider')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <%
                                    provider_config_list = []
                                    for curProvider in sickbeard.providers.sortedProviderList():
                                        if not curProvider.is_active:
                                            continue
                                        provider_config_list.append(curProvider)
                                %>
                                % if provider_config_list:
                                    <select id="editAProvider" class="form-control input-sm input250">
                                        % for cur_provider in provider_config_list:
                                            <option value="${cur_provider.get_id()}">${cur_provider.name}</option>
                                        % endfor
                                    </select>
                                % else:
                                    <label>${_('no providers available to configure.')}</label>
                                % endif
                            </div>
                        </div>


                        <!-- start div for editing providers //-->
                        % for curNewznabProvider in sickbeard.newznabProviderList:
                            <div class="providerDiv" id="${curNewznabProvider.get_id("Div")}">
                                % if curNewznabProvider.default and curNewznabProvider.needs_auth:

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" id="${curNewznabProvider.get_id("_url")}"
                                                   value="${curNewznabProvider.url}" class="form-control input-sm input350"
                                                   disabled autocapitalize="off"/>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('API key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" id="${curNewznabProvider.get_id("_hash")}"
                                                   value="${curNewznabProvider.key}"
                                                   newznab_name="${curNewznabProvider.get_id("_hash")}"
                                                   class="newznab_key form-control input-sm input350" autocapitalize="off"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curNewznabProvider, 'enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNewznabProvider.get_id("_enable_daily")}"
                                                   id="${curNewznabProvider.get_id("_enable_daily")}"
                                                   ${('', 'checked="checked"')[curNewznabProvider]}
                                                   ${('disabled', '')[curNewznabProvider.can_daily]}
                                            />
                                            <label for="${curNewznabProvider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not curNewznabProvider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curNewznabProvider, 'enable_backlog'):
                                    <div class="field-pair row${(' hidden', '')[curNewznabProvider.supports_backlog]}">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNewznabProvider.get_id("_enable_backlog")}"
                                                   id="${curNewznabProvider.get_id("_enable_backlog")}"
                                                   ${('', 'checked="checked"')[curNewznabProvider.config('backlog')]}
                                                   ${('disabled', '')[curNewznabProvider.can_backlog]}
                                            />
                                            <label for="${curNewznabProvider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not curNewznabProvider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curNewznabProvider, 'search_mode'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Season search mode')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label>${_('when searching for complete seasons you can choose to have it look for season packs only, or choose to have it build a complete season from just single episodes.')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curNewznabProvider.get_id("_search_mode")}"
                                                           id="${curNewznabProvider.get_id("_search_mode_sponly")}"
                                                           value="sponly" ${('', 'checked="checked"')[curNewznabProvider.search_mode=="sponly"]}/>
                                                    <label for="${curNewznabProvider.get_id("_search_mode_sponly")}">${_('season packs only.')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curNewznabProvider.get_id("_search_mode")}"
                                                           id="${curNewznabProvider.get_id("_search_mode_eponly")}"
                                                           value="eponly" ${('', 'checked="checked"')[curNewznabProvider.search_mode=="eponly"]}/>
                                                    <label for="${curNewznabProvider.get_id("_search_mode_eponly")}">${_('episodes only.')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curNewznabProvider, 'search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNewznabProvider.get_id("_search_fallback")}"
                                                   id="${curNewznabProvider.get_id("_search_fallback")}" ${('', 'checked="checked"')[curNewznabProvider.config('search_fallback')]}/>
                                            <label for="${curNewznabProvider.get_id("_search_fallback")}">${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                        % for curNzbProvider in [curProvider for curProvider in sickbeard.providers.sortedProviderList() if curProvider.provider_type == GenericProvider.NZB and curProvider not in sickbeard.newznabProviderList]:
                            <div class="providerDiv" id="${curNzbProvider.get_id("Div")}">
                                % if curNzbProvider.options('username'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curNzbProvider.get_id("_username")}"
                                                   value="${curNzbProvider.username}" class="form-control input-sm input350"
                                                   autocapitalize="off" autocomplete="no"/>
                                        </div>
                                    </div>
                                % endif

                                % if curNzbProvider.options('api_key'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('API key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curNzbProvider.get_id("_api_key")}"
                                                   value="${curNzbProvider.api_key}" class="form-control input-sm input350"
                                                   autocapitalize="off"/>
                                        </div>
                                    </div>
                                % endif

                                % if curNzbProvider.options('enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNzbProvider.get_id("_enable_daily")}"
                                                   id="${curNzbProvider.get_id("_enable_daily")}"
                                                   ${('', 'checked="checked"')[curNzbProvider.config('daily')]}
                                                   ${('disabled', '')[curNzbProvider.can_daily]}
                                            />
                                            <label for="${curNzbProvider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not curNzbProvider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if curNzbProvider.options('enable_backlog'):
                                    <div class="field-pair row${(' hidden', '')[curNzbProvider.supports_backlog]}">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNzbProvider.get_id("_enable_backlog")}"
                                                   id="${curNzbProvider.get_id("_enable_backlog")}"
                                                   ${('', ' checked="checked"')[curNzbProvider.config('backlog')]}
                                                   ${('disabled', ' ')[curNzbProvider.can_backlog]}
                                            />
                                            <label for="${curNzbProvider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not curNzbProvider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if curNzbProvider.options('search_mode'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Season search mode')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label>${_('when searching for complete seasons you can choose to have it look for season packs only, or choose to have it build a complete season from just single episodes.')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curNzbProvider.get_id("_search_mode")}"
                                                           id="${curNzbProvider.get_id("_search_mode_sponly")}"
                                                           value="sponly" ${('', 'checked="checked"')[curNzbProvider.search_mode=="sponly"]}/>
                                                    <label for="${curNzbProvider.get_id("_search_mode_sponly")}">season packs only.</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curNzbProvider.get_id("_search_mode")}"
                                                           id="${curNzbProvider.get_id("_search_mode_eponly")}"
                                                           value="eponly" ${('', 'checked="checked"')[curNzbProvider.search_mode=="eponly"]}/>
                                                    <label for="${curNzbProvider.get_id("_search_mode_eponly")}">episodes only.</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if curNzbProvider.options('search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNzbProvider.get_id("_search_fallback")}"
                                                   id="${curNzbProvider.get_id("_search_fallback")}" ${('', 'checked="checked"')[curNzbProvider.config('search_fallback')]}/>
                                            <label for="${curNzbProvider.get_id("_search_fallback")}">${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                        % for curTorrentProvider in [curProvider for curProvider in sickbeard.providers.sortedProviderList() if curProvider.provider_type == GenericProvider.TORRENT]:
                            <div class="providerDiv" id="${curTorrentProvider.get_id("Div")}">

                                % if curTorrentProvider.options('custom_url'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Custom URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_custom_url")}"
                                                   id="${curTorrentProvider.get_id("_custom_url")}"
                                                   value="${curTorrentProvider.config('custom_url')}"
                                                   class="form-control input-sm input350" autocapitalize="off"/>
                                            <label for="${curTorrentProvider.get_id("_custom_url")}">${_('the URL should include the protocol (and port if applicable).  Examples:  http://192.168.1.4/ or http://localhost:3000/')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('api_key'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Api key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_api_key")}"
                                                   id="${curTorrentProvider.get_id("_api_key")}"
                                                   value="${curTorrentProvider.config('api_key')}" class="form-control input-sm input350"
                                                   autocapitalize="off"/>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('username'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_username")}"
                                                   id="${curTorrentProvider.get_id("_username")}"
                                                   value="${curTorrentProvider.config('username')}" class="form-control input-sm input350"
                                                   autocapitalize="off" autocomplete="no"/>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('password'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input
                                                type="password" name="${curTorrentProvider.get_id("_password")}"
                                                id="${curTorrentProvider.get_id("_password")}" value="${curTorrentProvider.config('password')|hide}"
                                                class="form-control input-sm input350" autocomplete="no" autocapitalize="off"
                                            />
                                        </div>
                                    </div>
                                % endif
                                % if hasattr(curTorrentProvider, 'passkey'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Passkey')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input
                                                type="text" name="${curTorrentProvider.get_id("_passkey")}" id="${curTorrentProvider.get_id("_passkey")}"
                                                value="${curTorrentProvider.config('passkey')|hide}" class="form-control input-sm input350" autocapitalize="off"
                                            />
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('cookies'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Cookies')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="${curTorrentProvider.get_id("_cookies")}"
                                                           id="${curTorrentProvider.get_id("_cookies")}"
                                                           value="${curTorrentProvider.config('cookies')}"
                                                           class="form-control input-sm input350"
                                                           autocapitalize="off" autocomplete="no" />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="${curTorrentProvider.get_id("_cookies")}">
                                                        ${_('example: uid=1234;pass=567845439634987<br>' +
                                                        'note: uid and pass are not your username/password.<br>' +
                                                        'use DevTools or Firebug to get these values after logging in on your browser.')}
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('pin'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Pin')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input
                                                type="password" name="${curTorrentProvider.get_id("_pin")}"
                                                id="${curTorrentProvider.get_id("_pin")}" value="${curTorrentProvider.config('pin')|hide}"
                                                class="form-control input-sm input100" autocomplete="no" autocapitalize="off"
                                            />
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('ratio'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${curTorrentProvider.get_id("_ratio_desc")}">${_('Seed ratio')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="number" min="-1" step="0.1" name="${curTorrentProvider.get_id("_ratio")}"
                                                           id="${curTorrentProvider.get_id("_ratio")}" value="${curTorrentProvider.config('ratio')}"
                                                           class="form-control input-sm input75"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="${curTorrentProvider.get_id("_ratio")}">${_('stop transfer when ratio is reached<br>(-1 SickChill default to seed forever, or leave blank for downloader default)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('minseed'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${curTorrentProvider.get_id("_minseed_desc")}">${_('Minimum seeders')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="number" min="0" step="1" name="${curTorrentProvider.get_id("_minseed")}"
                                                   id="${curTorrentProvider.get_id("_minseed")}"
                                                    value="${curTorrentProvider.config('minseed')}" class="form-control input-sm input75"/>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('minleech'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${curTorrentProvider.get_id("_minleech_desc")}">${_('Minimum leechers')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="number" min="0" step="1" name="${curTorrentProvider.get_id("_minleech")}"
                                                   id="${curTorrentProvider.get_id("_minleech")}"
                                                    value="${curTorrentProvider.config('minleech')}"
                                                   class="form-control input-sm input75"/>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('confirmed'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Confirmed download')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_confirmed")}"
                                                   id="${curTorrentProvider.get_id("_confirmed")}" ${('', 'checked="checked"')[curTorrentProvider.config('confirmed')]}/>
                                            <label for="${curTorrentProvider.get_id("_confirmed")}">${_('only download torrents from trusted or verified uploaders ?')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('ranked'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Ranked torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_ranked")}"
                                                   id="${curTorrentProvider.get_id("_ranked")}" ${('', 'checked="checked"')[curTorrentProvider.config('ranked')]} />
                                            <label for="${curTorrentProvider.get_id("_ranked")}">${_('only download ranked torrents (trusted releases)')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('engrelease'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('English torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_engrelease")}"
                                                   id="${curTorrentProvider.get_id("_engrelease")}" ${('', 'checked="checked"')[curTorrentProvider.config('engrelease')]} />
                                            <label for="${curTorrentProvider.get_id("_engrelease")}">${_('only download english torrents, or torrents containing english subtitles')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('onlyspasearch'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('For Spanish torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_onlyspasearch")}"
                                                   id="${curTorrentProvider.get_id("_onlyspasearch")}" ${('', 'checked="checked"')[curTorrentProvider.config('onlyspasearch')]} />
                                            <label for="${curTorrentProvider.get_id("_onlyspasearch")}">${_('ONLY search on this provider if show info is defined as "Spanish" (avoid provider\'s use for VOS shows)')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('sorting'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Sorting results by')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="${curTorrentProvider.get_id("_sorting")}" id="${curTorrentProvider.get_id("_sorting")}" class="form-control input-sm input200">
                                                % for curAction in ('last', 'seeders', 'leechers'):
                                                    <option value="${curAction}" ${('', 'selected="selected"')[curAction == curTorrentProvider.config('sorting')]}>${curAction}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('freeleech'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Freeleech')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_freeleech")}"
                                                   id="${curTorrentProvider.get_id("_freeleech")}" ${('', 'checked="checked"')[curTorrentProvider.config('freeleech')]}/>
                                            <label for="${curTorrentProvider.get_id("_freeleech")}">${_('only download <b>"FreeLeech"</b> torrents.')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_enable_daily")}"
                                                   id="${curTorrentProvider.get_id("_enable_daily")}"
                                                   ${('', 'checked="checked"')[curTorrentProvider.config('daily')]}
                                                   ${('disabled', ' ')[curTorrentProvider.can_daily]}
                                            />
                                            <label for="${curTorrentProvider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not curTorrentProvider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('enable_backlog'):
                                    <div class="field-pair row${(' hidden', '')[curTorrentProvider.supports_backlog]}">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_enable_backlog")}"
                                                   id="${curTorrentProvider.get_id("_enable_backlog")}"
                                                   ${('', 'checked="checked"')[curTorrentProvider.config('backlog')]}
                                                   ${('disabled', '')[curTorrentProvider.can_backlog]}
                                            />

                                            <label for="${curTorrentProvider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not curTorrentProvider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('search_mode'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Season search mode')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label>${_('when searching for complete seasons you can choose to have it look for season packs only, or choose to have it build a complete season from just single episodes.')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curTorrentProvider.get_id("_search_mode")}"
                                                           id="${curTorrentProvider.get_id("_search_mode_sponly")}"
                                                           value="sponly" ${('', 'checked="checked"')[curTorrentProvider.config('search_mode')=="sponly"]}/>
                                                    <label for="${curTorrentProvider.get_id("_search_mode_sponly")}">season packs only.</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curTorrentProvider.get_id("_search_mode")}"
                                                           id="${curTorrentProvider.get_id("_search_mode_eponly")}"
                                                           value="eponly" ${('', 'checked="checked"')[curTorrentProvider.config('search_mode')=="eponly"]}/>
                                                    <label for="${curTorrentProvider.get_id("_search_mode_eponly")}">episodes only.</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_search_fallback")}"
                                                   id="${curTorrentProvider.get_id("_search_fallback")}" ${('', 'checked="checked"')[curTorrentProvider.config('search_fallback')]}/>
                                            <label for="${curTorrentProvider.get_id("_search_fallback")}">${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('cat') and curTorrentProvider.get_id() == 'tntvillage':
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Category')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="${curTorrentProvider.get_id("_cat")}"
                                                    id="${curTorrentProvider.get_id("_cat")}" class="form-control input-sm input200">
                                                % for i in curTorrentProvider.category_dict.keys():
                                                    <option value="${curTorrentProvider.category_dict[i]}" ${('', 'selected="selected"')[curTorrentProvider.category_dict[i] == curTorrentProvider.config('cat')]}>${i}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.options('subtitle') and curTorrentProvider.get_id() == 'tntvillage':
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Subtitled')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_subtitle")}"
                                                   id="${curTorrentProvider.get_id("_subtitle")}" ${('', 'checked="checked"')[curTorrentProvider.config('subtitle')]}/>
                                            <label for="${curTorrentProvider.get_id("_subtitle")}">${_('select torrent with Italian subtitle')}</label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                    </fieldset>
                </div>
            </div>
        </div>

        % if sickbeard.USE_NZBS:
            <div id="custom-newznab" class="component-group">
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <h3>${_('Configure Custom<br>Newznab Providers')}</h3>
                            <p>${_('Add and setup or remove custom Newznab providers.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                        <fieldset class="component-group-list">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Select provider')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="hidden" name="newznab_string" id="newznab_string"/>
                                    <select id="editANewznabProvider" class="form-control input-sm input200">
                                        <option value="addNewznab">${_('-- add new provider --')}</option>
                                    </select>
                                </div>
                            </div>

                            <div class="newznabProviderDiv" id="addNewznab">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Provider name')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="newznab_name" class="form-control input-sm input200"
                                               autocapitalize="off" title="Provider name"/>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Site URL')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="newznab_url" class="form-control input-sm input350"
                                               autocapitalize="off" title="Provider url"/>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('API key')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input
                                                    type="password" id="newznab_key" class="form-control input-sm input350" autocapitalize="off"
                                                />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="newznab_key" class="component-desc">(if not required, type 0)</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row" id="newznabcapdiv">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Newznab search categories')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select id="newznab_cap" multiple="multiple" style="min-width:10em;"></select>
                                                <select id="newznab_cat" multiple="multiple" style="min-width:10em;"></select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label><b>${_('select your Newznab categories on the left, and click the "update categories" button to use them for searching.) <b>don\'t forget to to save the form!')}</b></label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input class="btn newznab_cat_update" type="button" id="newznab_cat_update" value="${_('Update Categories')}" disabled="disabled" />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div id="newznab_add_div">
                                            <input class="btn newznab_save" type="button" id="newznab_add" value="${_('Add')}"/>
                                        </div>
                                        <div id="newznab_update_div" style="display: none;">
                                            <input class="btn btn-danger newznab_delete" type="button" id="newznab_delete" value="${_('Delete')}"/>
                                        </div>
                                    </div>
                                </div>

                            </div>

                        </fieldset>
                    </div>
                </div>
            </div>
        % endif

        % if sickbeard.USE_TORRENTS:
            <div id="custom-torrent" class="component-group">
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <h3>${_('Configure Custom Torrent Providers')}</h3>
                            <p>${_('Add and setup or remove custom RSS providers.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                        <fieldset class="component-group-list">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Select provider')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="hidden" name="torrentrss_string" id="torrentrss_string"/>
                                    <select id="editATorrentRssProvider" class="form-control input-sm input200">
                                        <option value="addTorrentRss">${_('-- add new provider --')}</option>
                                    </select>
                                </div>
                            </div>

                            <div class="torrentRssProviderDiv" id="addTorrentRss">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Provider name')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="torrentrss_name" class="form-control input-sm input200" autocapitalize="off"/>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('RSS URL')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="torrentrss_url" class="form-control input-sm input350" autocapitalize="off"/>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Cookies')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="torrentrss_cookies" class="form-control input-sm input350" autocapitalize="off"/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>eg. uid=xx;pass=yy</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Search element')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="torrentrss_title_tag" class="form-control input-sm input200" value="title" autocapitalize="off"/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <span class="component-desc">${_('eg: title')}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div id="torrentrss_add_div">
                                            <input type="button" class="btn torrentrss_save" id="torrentrss_add" value="${_('Add')}"/>
                                        </div>
                                        <div id="torrentrss_update_div" style="display: none;">
                                            <input type="button" class="btn btn-danger torrentrss_delete" id="torrentrss_delete" value="${_('Delete')}"/>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
        % endif

    </form>
</%block>
