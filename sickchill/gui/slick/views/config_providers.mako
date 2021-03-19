<%inherit file="/layouts/config.mako"/>
<%!
    from sickchill.oldbeard import providers
    from sickchill import settings
    from sickchill.oldbeard.filters import hide
    from sickchill.oldbeard.helpers import anon_url
    from sickchill.providers.GenericProvider import GenericProvider
%>

<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/configProviders.js')}"></script>
    <script type="text/javascript">
        $(document).ready(function() {
            $('#config-components').tabs();
            $('#config-components').on( "tabsactivate", function( event, ui ){
                if(ui.newPanel.selector === '#provider-options') {
                    //TODO: Reload provider options list
                }
            });
            % if settings.USE_NZBS:
                % for curNewznabProvider in settings.newznabProviderList:
                    $(this).addProvider('${curNewznabProvider.get_id()}', '${curNewznabProvider.name}', '${curNewznabProvider.url}', '${curNewznabProvider.key}', '${curNewznabProvider.catIDs}', ${int(curNewznabProvider.default)});
                % endfor
            % endif
            % if settings.USE_TORRENTS:
                % for curTorrentRssProvider in settings.torrentRssProviderList:
                    $(this).addTorrentRssProvider('${curTorrentRssProvider.get_id()}', '${curTorrentRssProvider.name}', '${curTorrentRssProvider.url}', '${curTorrentRssProvider.cookies}', '${curTorrentRssProvider.titleTAG}');
                % endfor
            % endif
        });
    </script>
</%block>

<%block name="tabs">
    <li><a href="#provider-priorities">${_('Provider Priorities')}</a></li>
    <li><a href="#provider-options">${_('Provider Options')}</a></li>

    % if settings.USE_NZBS:
        <li><a href="#custom-newznab">${_('Configure Custom Newznab Providers')}</a></li>
    % endif

    % if settings.USE_TORRENTS:
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

                        % if not settings.USE_NZBS or not settings.USE_TORRENTS:
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
                            % for curProvider in providers.sortedProviderList():
                            <%
                                if curProvider.provider_type == GenericProvider.NZB and not settings.USE_NZBS:
                                    continue
                                elif curProvider.provider_type == GenericProvider.TORRENT and not settings.USE_TORRENTS:
                                    continue

                                curName = curProvider.get_id()
                                if hasattr(curProvider, 'custom_url'):
                                    curURL = curProvider.custom_url or curProvider.url
                                else:
                                    curURL = curProvider.url
                            %>
                                <li class="ui-state-default ${('nzb-provider', 'torrent-provider')[curProvider.provider_type == GenericProvider.TORRENT]}" id="${curName}">
                                    <input type="checkbox" id="enable_${curName}" class="provider_enabler" ${('', 'checked="checked"')[curProvider.is_enabled]}/>
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
                                    <span class="ui-icon ${('ui-icon-locked','ui-icon-unlocked')[curProvider.public]} pull-right" style="vertical-align:middle;"></span>
                                </li>
                            % endfor
                        </ul>
                        <input type="hidden" name="provider_order" id="provider_order" value="${" ".join([x.get_id(':'+str(int(x.is_enabled))) for x in providers.sortedProviderList()])}" />
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
                                    for curProvider in providers.sortedProviderList():
                                        if curProvider.provider_type == GenericProvider.NZB and not (settings.USE_NZBS and curProvider.is_enabled):
                                            continue
                                        elif curProvider.provider_type == GenericProvider.TORRENT and not (settings.USE_TORRENTS and curProvider.is_enabled):
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
                        % for curNewznabProvider in settings.newznabProviderList:
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
                                                   ${('', 'checked="checked"')[curNewznabProvider.daily_enabled]}
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
                                                   ${('', 'checked="checked"')[curNewznabProvider.backlog_enabled]}
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
                                                   id="${curNewznabProvider.get_id("_search_fallback")}" ${('', 'checked="checked"')[curNewznabProvider.search_fallback_enabled]}/>
                                            <label for="${curNewznabProvider.get_id("_search_fallback")}">${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                        % for curNzbProvider in [curProvider for curProvider in providers.sortedProviderList() if curProvider.provider_type == GenericProvider.NZB and curProvider not in settings.newznabProviderList]:
                            <div class="providerDiv" id="${curNzbProvider.get_id("Div")}">
                                % if hasattr(curNzbProvider, 'username'):
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

                                % if hasattr(curNzbProvider, 'api_key'):
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

                                % if hasattr(curNzbProvider, 'enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNzbProvider.get_id("_enable_daily")}"
                                                   id="${curNzbProvider.get_id("_enable_daily")}"
                                                   ${('', 'checked="checked"')[curNzbProvider.daily_enabled]}
                                                   ${('disabled', '')[curNzbProvider.can_daily]}
                                            />
                                            <label for="${curNzbProvider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not curNzbProvider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curNzbProvider, 'enable_backlog'):
                                    <div class="field-pair row${(' hidden', '')[curNzbProvider.supports_backlog]}">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNzbProvider.get_id("_enable_backlog")}"
                                                   id="${curNzbProvider.get_id("_enable_backlog")}"
                                                   ${('', ' checked="checked"')[curNzbProvider.backlog_enabled]}
                                                   ${('disabled', ' ')[curNzbProvider.can_backlog]}
                                            />
                                            <label for="${curNzbProvider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not curNzbProvider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curNzbProvider, 'search_mode'):
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

                                % if hasattr(curNzbProvider, 'search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curNzbProvider.get_id("_search_fallback")}"
                                                   id="${curNzbProvider.get_id("_search_fallback")}" ${('', 'checked="checked"')[curNzbProvider.search_fallback_enabled]}/>
                                            <label for="${curNzbProvider.get_id("_search_fallback")}">${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                        % for curTorrentProvider in [curProvider for curProvider in providers.sortedProviderList() if curProvider.provider_type == GenericProvider.TORRENT]:
                            <div class="providerDiv" id="${curTorrentProvider.get_id("Div")}">

                                % if hasattr(curTorrentProvider, 'custom_url'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Custom URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_custom_url")}"
                                                   id="${curTorrentProvider.get_id("_custom_url")}"
                                                   value="${curTorrentProvider.custom_url}"
                                                   class="form-control input-sm input350" autocapitalize="off"/>
                                            <label for="${curTorrentProvider.get_id("_custom_url")}">${_('the URL should include the protocol (and port if applicable).  Examples:  http://192.168.1.4/ or http://localhost:3000/')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'api_key'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Api key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_api_key")}"
                                                   id="${curTorrentProvider.get_id("_api_key")}"
                                                   value="${curTorrentProvider.api_key}" class="form-control input-sm input350"
                                                   autocapitalize="off"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'digest'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Digest')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_digest")}"
                                                   id="${curTorrentProvider.get_id("_digest")}"
                                                   value="${curTorrentProvider.digest}" class="form-control input-sm input350"
                                                   autocapitalize="off"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'hash'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Hash')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_hash")}"
                                                   id="${curTorrentProvider.get_id("_hash")}" value="${curTorrentProvider.hash}"
                                                   class="form-control input-sm input350" autocapitalize="off"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'username'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${curTorrentProvider.get_id("_username")}"
                                                   id="${curTorrentProvider.get_id("_username")}"
                                                   value="${curTorrentProvider.username}" class="form-control input-sm input350"
                                                   autocapitalize="off" autocomplete="no"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'password'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input
                                                type="password" name="${curTorrentProvider.get_id("_password")}"
                                                id="${curTorrentProvider.get_id("_password")}" value="${curTorrentProvider.password|hide}"
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
                                                value="${curTorrentProvider.passkey|hide}" class="form-control input-sm input350" autocapitalize="off"
                                            />
                                        </div>
                                    </div>
                                % endif

                                % if curTorrentProvider.enable_cookies:
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Cookies')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="${curTorrentProvider.get_id("_cookies")}"
                                                           id="${curTorrentProvider.get_id("_cookies")}"
                                                           value="${curTorrentProvider.cookies}"
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

                                % if hasattr(curTorrentProvider, 'pin'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Pin')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input
                                                type="password" name="${curTorrentProvider.get_id("_pin")}"
                                                id="${curTorrentProvider.get_id("_pin")}" value="${curTorrentProvider.pin|hide}"
                                                class="form-control input-sm input100" autocomplete="no" autocapitalize="off"
                                            />
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'ratio'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${curTorrentProvider.get_id("_ratio_desc")}">${_('Seed ratio')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="number" min="-1" step="0.1" name="${curTorrentProvider.get_id("_ratio")}"
                                                           id="${curTorrentProvider.get_id("_ratio")}" value="${curTorrentProvider.ratio or 0}"
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

                                % if hasattr(curTorrentProvider, 'minseed'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${curTorrentProvider.get_id("_minseed_desc")}">${_('Minimum seeders')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="number" min="0" step="1" name="${curTorrentProvider.get_id("_minseed")}"
                                                   id="${curTorrentProvider.get_id("_minseed")}"
                                                    value="${curTorrentProvider.minseed}" class="form-control input-sm input75"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'minleech'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${curTorrentProvider.get_id("_minleech_desc")}">${_('Minimum leechers')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="number" min="0" step="1" name="${curTorrentProvider.get_id("_minleech")}"
                                                   id="${curTorrentProvider.get_id("_minleech")}"
                                                    value="${curTorrentProvider.minleech}"
                                                   class="form-control input-sm input75"/>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'confirmed'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Confirmed download')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_confirmed")}"
                                                   id="${curTorrentProvider.get_id("_confirmed")}" ${('', 'checked="checked"')[curTorrentProvider.confirmed]}/>
                                            <label for="${curTorrentProvider.get_id("_confirmed")}">${_('only download torrents from trusted or verified uploaders ?')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'ranked'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Ranked torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_ranked")}"
                                                   id="${curTorrentProvider.get_id("_ranked")}" ${('', 'checked="checked"')[curTorrentProvider.ranked]} />
                                            <label for="${curTorrentProvider.get_id("_ranked")}">${_('only download ranked torrents (trusted releases)')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'engrelease'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('English torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_engrelease")}"
                                                   id="${curTorrentProvider.get_id("_engrelease")}" ${('', 'checked="checked"')[curTorrentProvider.engrelease]} />
                                            <label for="${curTorrentProvider.get_id("_engrelease")}">${_('only download english torrents, or torrents containing english subtitles')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'onlyspasearch'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('For Spanish torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_onlyspasearch")}"
                                                   id="${curTorrentProvider.get_id("_onlyspasearch")}" ${('', 'checked="checked"')[curTorrentProvider.onlyspasearch]} />
                                            <label for="${curTorrentProvider.get_id("_onlyspasearch")}">${_('ONLY search on this provider if show info is defined as "Spanish" (avoid provider\'s use for VOS shows)')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'sorting'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Sorting results by')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="${curTorrentProvider.get_id("_sorting")}" id="${curTorrentProvider.get_id("_sorting")}" class="form-control input-sm input200">
                                                % for curAction in ('last', 'seeders', 'leechers'):
                                                    <option value="${curAction}" ${('', 'selected="selected"')[curAction == curTorrentProvider.sorting]}>${curAction}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'freeleech'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Freeleech')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_freeleech")}"
                                                   id="${curTorrentProvider.get_id("_freeleech")}" ${('', 'checked="checked"')[curTorrentProvider.freeleech]}/>
                                            <label for="${curTorrentProvider.get_id("_freeleech")}">${_('only download <b>"FreeLeech"</b> torrents.')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_enable_daily")}"
                                                   id="${curTorrentProvider.get_id("_enable_daily")}"
                                                   ${('', 'checked="checked"')[curTorrentProvider.daily_enabled]}
                                                   ${('disabled', ' ')[curTorrentProvider.can_daily]}
                                            />
                                            <label for="${curTorrentProvider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not curTorrentProvider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'enable_backlog'):
                                    <div class="field-pair row${(' hidden', '')[curTorrentProvider.supports_backlog]}">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_enable_backlog")}"
                                                   id="${curTorrentProvider.get_id("_enable_backlog")}"
                                                   ${('', 'checked="checked"')[curTorrentProvider.backlog_enabled]}
                                                   ${('disabled', '')[curTorrentProvider.can_backlog]}
                                            />

                                            <label for="${curTorrentProvider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not curTorrentProvider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'search_mode'):
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
                                                           value="sponly" ${('', 'checked="checked"')[curTorrentProvider.search_mode=="sponly"]}/>
                                                    <label for="${curTorrentProvider.get_id("_search_mode_sponly")}">season packs only.</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${curTorrentProvider.get_id("_search_mode")}"
                                                           id="${curTorrentProvider.get_id("_search_mode_eponly")}"
                                                           value="eponly" ${('', 'checked="checked"')[curTorrentProvider.search_mode=="eponly"]}/>
                                                    <label for="${curTorrentProvider.get_id("_search_mode_eponly")}">episodes only.</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_search_fallback")}"
                                                   id="${curTorrentProvider.get_id("_search_fallback")}" ${('', 'checked="checked"')[curTorrentProvider.search_fallback_enabled]}/>
                                            <label for="${curTorrentProvider.get_id("_search_fallback")}">${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'cat') and curTorrentProvider.get_id() == 'tntvillage':
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Category')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="${curTorrentProvider.get_id("_cat")}"
                                                    id="${curTorrentProvider.get_id("_cat")}" class="form-control input-sm input200">
                                                % for i in curTorrentProvider.category_dict.values():
                                                    <option value="${i}" ${('', 'selected="selected"')[i == curTorrentProvider.cat]}>${i}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                % endif

                                % if hasattr(curTorrentProvider, 'subtitle') and curTorrentProvider.get_id() == 'tntvillage':
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Subtitled')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${curTorrentProvider.get_id("_subtitle")}"
                                                   id="${curTorrentProvider.get_id("_subtitle")}" ${('', 'checked="checked"')[curTorrentProvider.subtitle]}/>
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

        % if settings.USE_NZBS:
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

        % if settings.USE_TORRENTS:
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
                                                <input type="text" id="torrentrss_titleTAG" class="form-control input-sm input200" value="title" autocapitalize="off"/>
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
