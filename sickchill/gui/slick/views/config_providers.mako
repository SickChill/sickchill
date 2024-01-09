<%inherit file="/layouts/config.mako" />
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
                % for provider in settings.newznab_provider_list:
                    $(this).addProvider('${provider.get_id()}', '${provider.name}', '${provider.url}', '${provider.key}', '${provider.categories}', ${int(provider.default)});
                % endfor
            % endif
            % if settings.USE_TORRENTS:
                % for provider in settings.torrent_rss_provider_list:
                    $(this).addTorrentRssProvider('${provider.get_id()}', '${provider.name}', '${provider.url}', '${provider.cookies}', '${provider.titleTAG}');
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
                                <b><a class="primary" href="/config/search">Search Settings</a></b></blockquote>
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
                            % for provider in providers.sorted_provider_list(only_enabled=True):
                            <%
                                if provider.has_option('custom_url'):
                                    provider_url = provider.custom_url or provider.url
                                else:
                                    provider_url = provider.url
                            %>
                                <li class="ui-state-default ${('nzb-provider', 'torrent-provider')[provider.provider_type == GenericProvider.TORRENT]}" id="${provider.get_id()}">
                                    <input type="checkbox" id="enable_${provider.get_id()}" name="enable_${provider.get_id()}" class="provider_enabler" ${checked(provider.is_enabled)} />
                                    <a href="${anon_url(provider_url)}" class="imgLink" rel="noreferrer" target="_blank">
                                        <img src="${static_url('images/providers/' + provider.image_name())}" alt="${provider.name}" title="${provider.name}" width="16" height="16" style="vertical-align:middle;" />
                                    </a>
                                    <label for="enable_${provider.get_id()}" style="vertical-align:middle;">${provider.name}</label>
                                    ${('<span class="red-text">*</span>', '')[provider.can_backlog]} ${('<span class="red-text">!</span>', '')[provider.can_daily]}
                                    <span class="ui-icon ui-icon-arrowthick-2-n-s pull-right" style="vertical-align:middle;"></span>
                                    <span class="ui-icon ${('ui-icon-locked','ui-icon-unlocked')[provider.public]} pull-right" style="vertical-align:middle;"></span>
                                </li>
                            % endfor
                        </ul>
                        <input type="hidden" name="provider_order" id="provider_order" value="${" ".join([x.get_id(':'+str(int(x.is_enabled))) for x in providers.sorted_provider_list()])}" />
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
                                    provider_config_list = providers.sorted_provider_list(only_enabled = True)
                                %>
                                % if any(provider.is_enabled for provider in provider_config_list):
                                    <select id="editAProvider" class="form-control input-sm input250">
                                        % for cur_provider in (provider for provider in provider_config_list if provider.is_enabled):
                                            <option value="${cur_provider.get_id()}">${cur_provider.name}</option>
                                        % endfor
                                    </select>
                                % else:
                                    <label>${_('No providers available to configure. You must enable either torrent or newznab first to enable providers.')}</label>
                                % endif
                            </div>
                        </div>


                        <!-- start div for editing providers //-->
                        % for provider in settings.newznab_provider_list:
                            <div class="providerDiv" id="${provider.get_id("Div")}">
                                % if provider.default and provider.needs_auth:

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" value="${provider.url}" class="form-control input-sm input350" disabled autocapitalize="off" />
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('API key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" value="${provider.key}" newznab_name="${provider.get_id("_hash")}" class="newznab_key form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_enable_daily")}" ${checked(provider.daily_enabled)} ${disabled(provider.can_daily)} />
                                            <label for="${provider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not provider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('enable_backlog'):
                                     <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_enable_backlog")}" ${checked(provider.backlog_enabled)} ${disabled(provider.can_backlog)} />
                                            <label for="${provider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not provider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('search_mode'):
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
                                                    <input type="radio" name="${provider.get_id("_search_mode")}" value="season" ${checked(provider.search_mode=="season")}/>
                                                    <label for="${provider.get_id("_search_mode_sponly")}">${_('season packs only.')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${provider.get_id("_search_mode")}" value="episode" ${checked(provider.search_mode=="episode")}/>
                                                    <label for="${provider.get_id("_search_mode_eponly")}">${_('episodes only.')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_search_fallback")}" id="${provider.get_id("_search_fallback")}" ${checked(provider.search_fallback_enabled)}/>
                                            <label for="${provider.get_id("_search_fallback")}">
                                                ${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}
                                            </label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                        % for provider in [provider for provider in providers.sorted_provider_list() if provider.provider_type == GenericProvider.NZB and provider not in settings.newznab_provider_list]:
                            <div class="providerDiv" id="${provider.get_id("Div")}">
                                % if provider.has_option('username'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_username")}" value="${provider.username}" class="form-control input-sm input350" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('api_key'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('API key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_api_key")}" value="${provider.api_key}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_enable_daily")}" ${checked(provider.daily_enabled)} ${disabled(provider.can_daily)} />
                                            <label for="${provider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not provider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('enable_backlog'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_enable_backlog")}" ${checked(provider.backlog_enabled)} ${disabled(provider.can_backlog)} />
                                            <label for="${provider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not provider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('search_mode'):
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
                                                    <input type="radio" name="${provider.get_id("_search_mode")}" id="${provider.get_id("_search_mode_sponly")}" value="season" ${checked(provider.search_mode=="season")}/>
                                                    <label for="${provider.get_id("_search_mode_sponly")}">season packs only.</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${provider.get_id("_search_mode")}" value="episode" ${checked(provider.search_mode=="episode")}/>
                                                    <label for="${provider.get_id("_search_mode_eponly")}">episodes only.</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_search_fallback")}" id="${provider.get_id("_search_fallback")}" ${checked(provider.search_fallback_enabled)}/>
                                            <label for="${provider.get_id("_search_fallback")}">
                                                ${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}
                                            </label>
                                        </div>
                                    </div>
                                % endif

                            </div>
                        % endfor

                        % for provider in [provider for provider in providers.sorted_provider_list() if provider.provider_type == GenericProvider.TORRENT]:
                            <div class="providerDiv" id="${provider.get_id("Div")}">

                                % if provider.has_option('custom_url'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Custom URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_custom_url")}" id="${provider.get_id("_custom_url")}" value="${provider.custom_url}" class="form-control input-sm input350" autocapitalize="off" />
                                            <label for="${provider.get_id("_custom_url")}">${_('the URL should include the protocol (and port if applicable).  Examples:  http://192.168.1.4/ or http://localhost:3000/')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('api_key'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Api key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_api_key")}" id="${provider.get_id("_api_key")}" value="${provider.api_key}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('digest'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Digest')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_digest")}" id="${provider.get_id("_digest")}" value="${provider.digest}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('hash'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Hash')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_hash")}" id="${provider.get_id("_hash")}" value="${provider.hash}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('username'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_username")}" id="${provider.get_id("_username")}" value="${provider.username}" class="form-control input-sm input350" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('password'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="password" name="${provider.get_id("_password")}" id="${provider.get_id("_password")}" value="${provider.password|hide}" class="form-control input-sm input350" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('passkey'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Passkey')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="text" name="${provider.get_id("_passkey")}" id="${provider.get_id("_passkey")}" value="${provider.passkey|hide}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.enable_cookies:
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Cookies')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="${provider.get_id("_cookies")}" id="${provider.get_id("_cookies")}" value="${provider.cookies}" class="form-control input-sm input350" autocapitalize="off" autocomplete="no" />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="${provider.get_id("_cookies")}">
                                                        ${_('example: uid=1234;pass=567845439634987<br>' +
                                                        'note: uid and pass are not your username/password.<br>' +
                                                        'use DevTools or Firebug to get these values after logging in on your browser.')}
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('pin'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Pin')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="password" name="${provider.get_id("_pin")}" id="${provider.get_id("_pin")}" value="${provider.pin|hide}" class="form-control input-sm input100" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('ratio'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${provider.get_id("_ratio_desc")}">${_('Seed ratio')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="number" min="-1" step="0.1" name="${provider.get_id("_ratio")}" id="${provider.get_id("_ratio")}" value="${provider.ratio or 0}" class="form-control input-sm input75" />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="${provider.get_id("_ratio")}">${_('stop transfer when ratio is reached<br>(-1 SickChill default to seed forever, or leave blank for downloader default)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('minseed'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${provider.get_id("_minseed_desc")}">${_('Minimum seeders')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="number" min="0" step="1" name="${provider.get_id("_minseed")}" value="${provider.minseed}" class="form-control input-sm input75" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('minleech'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="${provider.get_id("_minleech_desc")}">${_('Minimum leechers')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="number" min="0" step="1" name="${provider.get_id("_minleech")}" value="${provider.minleech}" class="form-control input-sm input75" />
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('confirmed'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Confirmed download')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_confirmed")}" id="${provider.get_id("_confirmed")}" ${checked(provider.confirmed)}/>
                                            <label for="${provider.get_id("_confirmed")}">${_('only download torrents from trusted or verified uploaders ?')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('ranked'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Ranked torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_ranked")}" id="${provider.get_id("_ranked")}" ${checked(provider.ranked)} />
                                            <label for="${provider.get_id("_ranked")}">${_('only download ranked torrents (trusted releases)')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('engrelease'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('English torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_engrelease")}" id="${provider.get_id("_engrelease")}" ${checked(provider.engrelease)} />
                                            <label for="${provider.get_id("_engrelease")}">${_('only download english torrents, or torrents containing english subtitles')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('onlyspasearch'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('For Spanish torrents')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_onlyspasearch")}" id="${provider.get_id("_onlyspasearch")}" ${checked(provider.onlyspasearch)} />
                                            <label for="${provider.get_id("_onlyspasearch")}">${_('ONLY search on this provider if show info is defined as "Spanish" (avoid provider\'s use for VOS shows)')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('sorting'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Sorting results by')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="${provider.get_id("_sorting")}" id="${provider.get_id("_sorting")}" class="form-control input-sm input200">
                                                % for curAction in ('last', 'seeders', 'leechers'):
                                                    <option value="${curAction}" ${selected(curAction == provider.sorting)}>${curAction}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('freeleech'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Freeleech')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_freeleech")}" id="${provider.get_id("_freeleech")}" ${checked(provider.freeleech)} />
                                            <label for="${provider.get_id("_freeleech")}">${_('only download <b>"FreeLeech"</b> torrents.')}</label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('enable_daily'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable daily searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_enable_daily")}" ${checked(provider.daily_enabled)} ${disabled(provider.can_daily)} />
                                            <label for="${provider.get_id("_enable_daily")}">${_('enable provider to perform daily searches.')}</label>
                                            % if not provider.can_daily:
                                              <p class="note"><span class="red-text">${_('Daily search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('enable_backlog'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable backlog searches')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_enable_backlog")}" ${checked(provider.backlog_enabled)} ${disabled(provider.can_backlog)} />

                                            <label for="${provider.get_id("_enable_backlog")}">${_('enable provider to perform backlog searches.')}</label>
                                            % if not provider.can_backlog:
                                              <p class="note"><span class="red-text">${_('Backlog search is currently not working on this provider')}</span></p>
                                            % endif
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('search_mode'):
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
                                                    <input type="radio" name="${provider.get_id("_search_mode")}" value="season" ${checked(provider.search_mode=="season")}/>
                                                    <label for="${provider.get_id("_search_mode_sponly")}">season packs only.</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="radio" name="${provider.get_id("_search_mode")}" value="episode" ${checked(provider.search_mode=="episode")}/>
                                                    <label for="${provider.get_id("_search_mode_eponly")}">episodes only.</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('search_fallback'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Enable fallback')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_search_fallback")}" id="${provider.get_id("_search_fallback")}" ${checked(provider.search_fallback_enabled)}/>
                                            <label for="${provider.get_id("_search_fallback")}">
                                                ${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}
                                            </label>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('cat'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Category')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="${provider.get_id("_cat")}" id="${provider.get_id("_cat")}" class="form-control input-sm input200">
                                                % for i in provider.category_dict.values():
                                                    <option value="${i}" ${selected(i == provider.cat)}>${i}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                % endif

                                % if provider.has_option('subtitle'):
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Subtitled')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="${provider.get_id("_subtitle")}" id="${provider.get_id("_subtitle")}" ${checked(provider.subtitle)}/>
                                            <label for="${provider.get_id("_subtitle")}">${_('select torrent with Italian subtitle')}</label>
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
                                    <input type="hidden" name="newznab_string" id="newznab_string" />
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
                                        <input type="text" id="newznab_name" class="form-control input-sm input200" autocapitalize="off" title="Provider name" />
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Site URL')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="newznab_url" class="form-control input-sm input350" autocapitalize="off" title="Provider url" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('API key')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="password" id="newznab_key" class="form-control input-sm input350" autocapitalize="off" />
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
                                                <input class="btn newznab_cat_update" type="button" id="newznab_cat_update" value="${_('Update Categories')}" disabled />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div id="newznab_add_div">
                                            <input class="btn newznab_save" type="button" id="newznab_add" value="${_('Add')}" />
                                        </div>
                                        <div id="newznab_update_div" style="display: none;">
                                            <input class="btn btn-danger newznab_delete" type="button" id="newznab_delete" value="${_('Delete')}" />
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
                                    <input type="hidden" name="torrent_rss_string" id="torrent_rss_string" />
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
                                        <input type="text" id="torrentrss_name" class="form-control input-sm input200" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('RSS URL')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="torrentrss_url" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Cookies')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="torrentrss_cookies" class="form-control input-sm input350" autocapitalize="off" />
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
                                                <input type="text" id="torrentrss_titleTAG" class="form-control input-sm input200" value="title" autocapitalize="off" />
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
                                            <input type="button" class="btn torrentrss_save" id="torrentrss_add" value="${_('Add')}" />
                                        </div>
                                        <div id="torrentrss_update_div" style="display: none;">
                                            <input type="button" class="btn btn-danger torrentrss_delete" id="torrentrss_delete" value="${_('Delete')}" />
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
