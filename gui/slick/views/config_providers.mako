<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
    from sickrage.providers.GenericProvider import GenericProvider
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/configProviders.js"></script>
<script type="text/javascript">
$(document).ready(function(){
    % if sickbeard.USE_NZBS:
        var show_nzb_providers = ${("false", "true")[bool(sickbeard.USE_NZBS)]};
        % for cur_newznab_provider in sickbeard.newznabProviderList:
        $(this).addProvider('${cur_newznab_provider.get_id()}', '${cur_newznab_provider.name}', '${cur_newznab_provider.url}', '${cur_newznab_provider.key}', '${cur_newznab_provider.catIDs}', ${int(cur_newznab_provider.default)}, show_nzb_providers);
        % endfor
    % endif
    % if sickbeard.USE_TORRENTS:
        % for cur_torrent_rss_provider in sickbeard.torrentRssProviderList:
        $(this).addTorrentRssProvider('${cur_torrent_rss_provider.get_id()}', '${cur_torrent_rss_provider.name}', '${cur_torrent_rss_provider.url}', '${cur_torrent_rss_provider.cookies}', '${cur_torrent_rss_provider.titleTAG}');
        % endfor
    % endif
});
$('#config-components').tabs();
</script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif
<div id="config">
    <div id="config-content">

        <form id="configForm" action="saveProviders" method="post">

            <div id="config-components">
                <ul>
                    <li><a href="#provider-priorities">${_('Provider Priorities')}</a></li>
                    <li><a href="#provider-options">${_('Provider Options')}</a></li>
                  % if sickbeard.USE_NZBS:
                    <li><a href="#custom-newznab">${_('Configure Custom Newznab Providers')}</a></li>
                  % endif
                  % if sickbeard.USE_TORRENTS:
                    <li><a href="#custom-torrent">${_('Configure Custom Torrent Providers')}</a></li>
                  % endif
                </ul>

                <div id="provider-priorities" class="component-group" style='min-height: 550px;'>

                    <div class="component-group-desc">
                        <h3>${_('Provider Priorities')}</h3>
                        <p>${_('Check off and drag the providers into the order you want them to be used.')}</p>
                        <p>${_('At least one provider is required but two are recommended.')}</p>

                        % if not sickbeard.USE_NZBS or not sickbeard.USE_TORRENTS:
                        <blockquote style="margin: 20px 0;">NZB/${_('Torrent providers can be toggled in ')}<b><a href="${srRoot}/config/search">Search Settings</a></b></blockquote>
                        % else:
                        <br>
                        % endif

                        <div>
                            <p class="note"><span class="red-text">*</span> ${_('Provider does not support backlog searches at this time.')}</p>
                            <p class="note"><span class="red-text">!</span> ${_('Provider is <b>NOT WORKING</b>.')}</p>
                        </div>
                    </div>

                    <fieldset class="component-group-list">
                        <ul id="provider_order_list">
                        % for cur_provider in sickbeard.providers.sortedProviderList():
                            <%
                                ## These will show the '!' not saying they are broken
                                broken_providers = {}
                                if cur_provider.provider_type == GenericProvider.NZB and not sickbeard.USE_NZBS:
                                    continue
                                elif cur_provider.provider_type == GenericProvider.TORRENT and not sickbeard.USE_TORRENTS:
                                    continue

                                cur_name = cur_provider.get_id()
                                if hasattr(cur_provider, 'custom_url'):
                                    cur_url = cur_provider.custom_url or cur_provider.url
                                else:
                                    cur_url = cur_provider.url
                            %>
                            <li class="ui-state-default ${('nzb-provider', 'torrent-provider')[bool(cur_provider.provider_type == GenericProvider.TORRENT)]}" id="${cur_name}">
                                <input type="checkbox" id="enable_${cur_name}" class="provider_enabler" ${('', 'checked="checked"')[cur_provider.is_enabled() is True]}/>
                                <a href="${anon_url(cur_url)}" class="imgLink" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;"><img src="${srRoot}/images/providers/${cur_provider.image_name()}" alt="${cur_provider.name}" title="${cur_provider.name}" width="16" height="16" style="vertical-align:middle;"/></a>
                                <span style="vertical-align:middle;">${cur_provider.name}</span>
                                ${('<span class="red-text">*</span>', '')[bool(cur_provider.supports_backlog)]}
                                ${('<span class="red-text">!</span>', '')[bool(cur_provider.get_id() not in broken_providers)]}
                                <span class="ui-icon ui-icon-arrowthick-2-n-s pull-right" style="vertical-align:middle;"></span>
                                <span class="ui-icon ${('ui-icon-locked','ui-icon-unlocked')[bool(cur_provider.public)]} pull-right" style="vertical-align:middle;"></span>
                            </li>
                        % endfor
                        </ul>
                        <input type="hidden" name="provider_order" id="provider_order" value="${" ".join([x.get_id()+':'+str(int(x.is_enabled())) for x in sickbeard.providers.sortedProviderList()])}"/>
                        <br><input type="submit" class="btn config_submitter" value="${_('Save Changes')}" /><br>
                    </fieldset>
                </div><!-- /component-group1 //-->

                <div id="provider-options" class="component-group">

                    <div class="component-group-desc">
                        <h3>${_('Provider Options')}</h3>
                        <p>${_('Configure individual provider settings here.')}</p>
                        <p>${_('Check with provider\'s website on how to obtain an API key if needed.')}</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="editAProvider" id="provider-list">
                                <span class="component-title">${_('Configure provider')}:</span>
                                <span class="component-desc">
                                    <%
                                        provider_config_list = []
                                        for cur_provider in sickbeard.providers.sortedProviderList():
                                            if cur_provider.provider_type == GenericProvider.NZB and (not sickbeard.USE_NZBS or not cur_provider.is_enabled()):
                                                continue
                                            elif cur_provider.provider_type == GenericProvider.TORRENT and ( not sickbeard.USE_TORRENTS or not cur_provider.is_enabled()):
                                                continue
                                            provider_config_list.append(cur_provider)
                                    %>
                                    % if provider_config_list:
                                        <select id="editAProvider" class="form-control input-sm">
                                            % for cur_provider in provider_config_list:
                                                <option value="${cur_provider.get_id()}">${cur_provider.name}</option>
                                            % endfor
                                        </select>
                                    % else:
                                        ${_('No providers available to configure.')}
                                    % endif
                                </span>
                            </label>
                        </div>


                    <!-- start div for editing providers //-->
                    % for cur_newznab_provider in [cur_provider for cur_provider in sickbeard.newznabProviderList]:
                    <div class="providerDiv" id="${cur_newznab_provider.get_id()}Div">
                        % if cur_newznab_provider.default and cur_newznab_provider.needs_auth:
                        <div class="field-pair">
                            <label for="${cur_newznab_provider.get_id()}_url">
                                <span class="component-title">URL:</span>
                                <span class="component-desc">
                                    <input type="text" id="${cur_newznab_provider.get_id()}_url" value="${cur_newznab_provider.url}" class="form-control input-sm input350" disabled autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="${cur_newznab_provider.get_id()}_hash">
                                <span class="component-title">API key:</span>
                                <span class="component-desc">
                                    <input type="text" id="${cur_newznab_provider.get_id()}_hash" value="${cur_newznab_provider.key}" newznab_name="${cur_newznab_provider.get_id()}_hash" class="newznab_key form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_newznab_provider, 'enable_daily'):
                        <div class="field-pair">
                            <label for="${cur_newznab_provider.get_id()}_enable_daily">
                                <span class="component-title">${_('Enable daily searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_newznab_provider.get_id()}_enable_daily" id="${cur_newznab_provider.get_id()}_enable_daily" ${('', 'checked="checked"')[bool(cur_newznab_provider.enable_daily)]}/>
                                    <p>${_('enable provider to perform daily searches.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_newznab_provider, 'enable_backlog'):
                        <div class="field-pair${(' hidden', '')[cur_newznab_provider.supports_backlog]}">
                            <label for="${cur_newznab_provider.get_id()}_enable_backlog">
                                <span class="component-title">${_('Enable backlog searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_newznab_provider.get_id()}_enable_backlog" id="${cur_newznab_provider.get_id()}_enable_backlog" ${('', 'checked="checked"')[bool(cur_newznab_provider.enable_backlog and cur_newznab_provider.supports_backlog)]}/>
                                    <p>${_('enable provider to perform backlog searches.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_newznab_provider, 'search_mode'):
                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Season search mode')}</span>
                                <span class="component-desc">
                                    <p>${_('when searching for complete seasons you can choose to have it look for season packs only, or choose to have it build a complete season from just single episodes.')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${cur_newznab_provider.get_id()}_search_mode" id="${cur_newznab_provider.get_id()}_search_mode_sponly" value="sponly" ${('', 'checked="checked"')[cur_newznab_provider.search_mode=="sponly"]}/>season packs only.
                                </span>
                            </label>
                            <label>
                                <span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${cur_newznab_provider.get_id()}_search_mode" id="${cur_newznab_provider.get_id()}_search_mode_eponly" value="eponly" ${('', 'checked="checked"')[cur_newznab_provider.search_mode=="eponly"]}/>episodes only.
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_newznab_provider, 'search_fallback'):
                        <div class="field-pair">
                            <label for="${cur_newznab_provider.get_id()}_search_fallback">
                                <span class="component-title">${_('Enable fallback')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_newznab_provider.get_id()}_search_fallback" id="${cur_newznab_provider.get_id()}_search_fallback" ${('', 'checked="checked"')[bool(cur_newznab_provider.search_fallback)]}/>
                                    <p>${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                    </div>
                    % endfor

                    % for cur_nzb_provider in [cur_provider for cur_provider in sickbeard.providers.sortedProviderList() if cur_provider.provider_type == GenericProvider.NZB and cur_provider not in sickbeard.newznabProviderList]:
                    <div class="providerDiv" id="${cur_nzb_provider.get_id()}Div">
                        % if hasattr(cur_nzb_provider, 'username'):
                        <div class="field-pair">
                            <label for="${cur_nzb_provider.get_id()}_username">
                                <span class="component-title">${_('Username')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_nzb_provider.get_id()}_username" value="${cur_nzb_provider.username}" class="form-control input-sm input350" autocapitalize="off" autocomplete="no" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_nzb_provider, 'api_key'):
                        <div class="field-pair">
                            <label for="${cur_nzb_provider.get_id()}_api_key">
                                <span class="component-title">${_('API key')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_nzb_provider.get_id()}_api_key" value="${cur_nzb_provider.api_key}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif


                        % if hasattr(cur_nzb_provider, 'enable_daily'):
                        <div class="field-pair">
                            <label for="${cur_nzb_provider.get_id()}_enable_daily">
                                <span class="component-title">${_('Enable daily searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_nzb_provider.get_id()}_enable_daily" id="${cur_nzb_provider.get_id()}_enable_daily" ${('', 'checked="checked"')[bool(cur_nzb_provider.enable_daily)]}/>
                                    <p>${_('enable provider to perform daily searches.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_nzb_provider, 'enable_backlog'):
                        <div class="field-pair${(' hidden', '')[cur_nzb_provider.supports_backlog]}">
                            <label for="${cur_nzb_provider.get_id()}_enable_backlog">
                                <span class="component-title">${_('Enable backlog searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_nzb_provider.get_id()}_enable_backlog" id="${cur_nzb_provider.get_id()}_enable_backlog" ${('', 'checked="checked"')[bool(cur_nzb_provider.enable_backlog and cur_nzb_provider.supports_backlog)]}/>
                                    <p>${_('enable provider to perform backlog searches.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_nzb_provider, 'search_mode'):
                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Season search mode')}</span>
                                <span class="component-desc">
                                    <p>${_('when searching for complete seasons you can choose to have it look for season packs only, or choose to have it build a complete season from just single episodes.')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${cur_nzb_provider.get_id()}_search_mode" id="${cur_nzb_provider.get_id()}_search_mode_sponly" value="sponly" ${('', 'checked="checked"')[cur_nzb_provider.search_mode=="sponly"]}/>season packs only.
                                </span>
                            </label>
                            <label>
                                <span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${cur_nzb_provider.get_id()}_search_mode" id="${cur_nzb_provider.get_id()}_search_mode_eponly" value="eponly" ${('', 'checked="checked"')[cur_nzb_provider.search_mode=="eponly"]}/>episodes only.
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_nzb_provider, 'search_fallback'):
                        <div class="field-pair">
                            <label for="${cur_nzb_provider.get_id()}_search_fallback">
                                <span class="component-title">${_('Enable fallback')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_nzb_provider.get_id()}_search_fallback" id="${cur_nzb_provider.get_id()}_search_fallback" ${('', 'checked="checked"')[bool(cur_nzb_provider.search_fallback)]}/>
                                    <p>${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                    </div>
                    % endfor

                    % for cur_torrent_provider in [cur_provider for cur_provider in sickbeard.providers.sortedProviderList() if cur_provider.provider_type == GenericProvider.TORRENT]:
                    <div class="providerDiv" id="${cur_torrent_provider.get_id()}Div">

                        % if hasattr(cur_torrent_provider, 'custom_url'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_custom_url">
                                <span class="component-title">${_('Custom URL')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_torrent_provider.get_id()}_custom_url" id="${cur_torrent_provider.get_id()}_custom_url" value="${cur_torrent_provider.custom_url}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">
                                    <p>${_('The URL should include the protocol (and port if applicable).  Examples:  http://192.168.1.4/ or http://localhost:3000/')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'api_key'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_api_key">
                                <span class="component-title">${_('Api key')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_torrent_provider.get_id()}_api_key" id="${cur_torrent_provider.get_id()}_api_key" value="${cur_torrent_provider.api_key}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'digest'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_digest">
                                <span class="component-title">${_('Digest')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_torrent_provider.get_id()}_digest" id="${cur_torrent_provider.get_id()}_digest" value="${cur_torrent_provider.digest}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'hash'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_hash">
                                <span class="component-title">${_('Hash')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_torrent_provider.get_id()}_hash" id="${cur_torrent_provider.get_id()}_hash" value="${cur_torrent_provider.hash}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'username'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_username">
                                <span class="component-title">${_('Username')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_torrent_provider.get_id()}_username" id="${cur_torrent_provider.get_id()}_username" value="${cur_torrent_provider.username}" class="form-control input-sm input350" autocapitalize="off" autocomplete="no" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'password'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_password">
                                <span class="component-title">${_('Password')}:</span>
                                <span class="component-desc">
                                    <input type="password" name="${cur_torrent_provider.get_id()}_password" id="${cur_torrent_provider.get_id()}_password" value="${cur_torrent_provider.password}" class="form-control input-sm input350" autocomplete="no" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'passkey'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_passkey">
                                <span class="component-title">${_('Passkey')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${cur_torrent_provider.get_id()}_passkey" id="${cur_torrent_provider.get_id()}_passkey" value="${cur_torrent_provider.passkey}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'pin'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_pin">
                                <span class="component-title">${_('Pin')}:</span>
                                <span class="component-desc">
                                    <input type="password" name="${cur_torrent_provider.get_id()}_pin" id="${cur_torrent_provider.get_id()}_pin" value="${cur_torrent_provider.pin}" class="form-control input-sm input100" autocomplete="no" autocapitalize="off" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'ratio'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_ratio">
                                <span class="component-title" id="${cur_torrent_provider.get_id()}_ratio_desc">${_('Seed ratio')}:</span>
                                <span class="component-desc">
                                    <input type="number" min="-1" step="0.1" name="${cur_torrent_provider.get_id()}_ratio" id="${cur_torrent_provider.get_id()}_ratio" value="${cur_torrent_provider.ratio}" class="form-control input-sm input75" />
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">
                                    <p>${_('stop transfer when ratio is reached<br>(-1 SickRage default to seed forever, or leave blank for downloader default)')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'minseed'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_minseed">
                                <span class="component-title" id="${cur_torrent_provider.get_id()}_minseed_desc">${_('Minimum seeders')}:</span>
                                <span class="component-desc">
                                    <input type="number" min="0" step="1" name="${cur_torrent_provider.get_id()}_minseed" id="${cur_torrent_provider.get_id()}_minseed" value="${cur_torrent_provider.minseed}" class="form-control input-sm input75" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'minleech'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_minleech">
                                <span class="component-title" id="${cur_torrent_provider.get_id()}_minleech_desc">${_('Minimum leechers')}:</span>
                                <span class="component-desc">
                                    <input type="number" min="0" step="1" name="${cur_torrent_provider.get_id()}_minleech" id="${cur_torrent_provider.get_id()}_minleech" value="${cur_torrent_provider.minleech}" class="form-control input-sm input75" />
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'confirmed'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_confirmed">
                                <span class="component-title">${_('Confirmed download')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_confirmed" id="${cur_torrent_provider.get_id()}_confirmed" ${('', 'checked="checked"')[bool(cur_torrent_provider.confirmed)]}/>
                                    <p>${_('only download torrents from trusted or verified uploaders ?')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'ranked'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_ranked">
                                <span class="component-title">${_('Ranked torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_ranked" id="${cur_torrent_provider.get_id()}_ranked" ${('', 'checked="checked"')[bool(cur_torrent_provider.ranked)]} />
                                    <p>${_('only download ranked torrents (trusted releases)')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'engrelease'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_engrelease">
                                <span class="component-title">${_('English torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_engrelease" id="${cur_torrent_provider.get_id()}_engrelease" ${('', 'checked="checked"')[bool(cur_torrent_provider.engrelease)]} />
                                    <p>${_('only download english torrents, or torrents containing english subtitles')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'onlyspasearch'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_onlyspasearch">
                                <span class="component-title">${_('For Spanish torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_onlyspasearch" id="${cur_torrent_provider.get_id()}_onlyspasearch" ${('', 'checked="checked"')[bool(cur_torrent_provider.onlyspasearch)]} />
                                    <p>${_('ONLY search on this provider if show info is defined as "Spanish" (avoid provider\'s use for VOS shows)')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'sorting'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_sorting">
                                <span class="component-title">${_('Sorting results by')}</span>
                                <span class="component-desc">
                                    <select name="${cur_torrent_provider.get_id()}_sorting" id="${cur_torrent_provider.get_id()}_sorting" class="form-control input-sm">
                                    % for cur_action in ('last', 'seeders', 'leechers'):
                                    <option value="${cur_action}" ${('', 'selected="selected"')[cur_action == cur_torrent_provider.sorting]}>${cur_action}</option>
                                    % endfor
                                    </select>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'freeleech'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_freeleech">
                                <span class="component-title">${_('Freeleech')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_freeleech" id="${cur_torrent_provider.get_id()}_freeleech" ${('', 'checked="checked"')[bool(cur_torrent_provider.freeleech)]}/>
                                    <p>${_('only download <b>"FreeLeech"</b> torrents.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'enable_daily'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_enable_daily">
                                <span class="component-title">${_('Enable daily searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_enable_daily" id="${cur_torrent_provider.get_id()}_enable_daily" ${('', 'checked="checked"')[bool(cur_torrent_provider.enable_daily)]}/>
                                    <p>${_('enable provider to perform daily searches.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'enable_backlog'):
                        <div class="field-pair${(' hidden', '')[cur_torrent_provider.supports_backlog]}">
                            <label for="${cur_torrent_provider.get_id()}_enable_backlog">
                                <span class="component-title">${_('Enable backlog searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_enable_backlog" id="${cur_torrent_provider.get_id()}_enable_backlog" ${('', 'checked="checked"')[bool(cur_torrent_provider.enable_backlog and cur_torrent_provider.supports_backlog)]}/>
                                    <p>${_('enable provider to perform backlog searches.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'search_mode'):
                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Season search mode')}</span>
                                <span class="component-desc">
                                    <p>${_('when searching for complete seasons you can choose to have it look for season packs only, or choose to have it build a complete season from just single episodes.')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${cur_torrent_provider.get_id()}_search_mode" id="${cur_torrent_provider.get_id()}_search_mode_sponly" value="sponly" ${('', 'checked="checked"')[cur_torrent_provider.search_mode=="sponly"]}/>season packs only.
                                </span>
                            </label>
                            <label>
                                <span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${cur_torrent_provider.get_id()}_search_mode" id="${cur_torrent_provider.get_id()}_search_mode_eponly" value="eponly" ${('', 'checked="checked"')[cur_torrent_provider.search_mode=="eponly"]}/>episodes only.
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'search_fallback'):
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_search_fallback">
                                <span class="component-title">${_('Enable fallback')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_search_fallback" id="${cur_torrent_provider.get_id()}_search_fallback" ${('', 'checked="checked"')[bool(cur_torrent_provider.search_fallback)]}/>
                                    <p>${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'cat') and cur_torrent_provider.get_id() == 'tntvillage':
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_cat">
                                <span class="component-title">${_('Category')}:</span>
                                <span class="component-desc">
                                    <select name="${cur_torrent_provider.get_id()}_cat" id="${cur_torrent_provider.get_id()}_cat" class="form-control input-sm">
                                        % for i in cur_torrent_provider.category_dict.keys():
                                        <option value="${cur_torrent_provider.category_dict[i]}" ${('', 'selected="selected"')[cur_torrent_provider.category_dict[i] == cur_torrent_provider.cat]}>${i}</option>
                                        % endfor
                                    </select>
                                </span>
                           </label>
                        </div>
                        % endif

                        % if hasattr(cur_torrent_provider, 'subtitle') and cur_torrent_provider.get_id() == 'tntvillage':
                        <div class="field-pair">
                            <label for="${cur_torrent_provider.get_id()}_subtitle">
                                <span class="component-title">${_('Subtitled')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${cur_torrent_provider.get_id()}_subtitle" id="${cur_torrent_provider.get_id()}_subtitle" ${('', 'checked="checked"')[bool(cur_torrent_provider.subtitle)]}/>
                                    <p>${_('select torrent with Italian subtitle')}</p>
                                </span>
                            </label>
                        </div>
                        % endif

                    </div>
                    % endfor


                    <!-- end div for editing providers -->

                    <input type="submit" class="btn config_submitter" value="Save Changes" /><br>

                    </fieldset>
                </div><!-- /component-group2 //-->

                % if sickbeard.USE_NZBS:
                <div id="custom-newznab" class="component-group">

                    <div class="component-group-desc">
                        <h3>${_('Configure Custom<br>Newznab Providers')}</h3>
                        <p>${_('Add and setup or remove custom Newznab providers.')}</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="newznab_string">
                                <span class="component-title">${_('Select provider')}:</span>
                                <span class="component-desc">
                                    <input type="hidden" name="newznab_string" id="newznab_string" />
                                    <select id="editANewznabProvider" class="form-control input-sm">
                                        <option value="addNewznab">${_('-- add new provider --')}</option>
                                    </select>
                                </span>
                            </label>
                        </div>

                    <div class="newznabProviderDiv" id="addNewznab">
                        <div class="field-pair">
                            <label for="newznab_name">
                                <span class="component-title">${_('Provider name')}:</span>
                                <input type="text" id="newznab_name" class="form-control input-sm input200" autocapitalize="off" />
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="newznab_url">
                                <span class="component-title">${_('Site URL')}:</span>
                                <input type="text" id="newznab_url" class="form-control input-sm input350" autocapitalize="off" />
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="newznab_key">
                                <span class="component-title">${_('API key')}:</span>
                                <input type="password" id="newznab_key" class="form-control input-sm input350" autocapitalize="off" />
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">(if not required, type 0)</span>
                            </label>
                        </div>

                        <div class="field-pair" id="newznabcapdiv">
                            <label>
                                <span class="component-title">${_('Newznab search categories')}:</span>
                                <select id="newznab_cap" multiple="multiple" style="min-width:10em;" ></select>
                                <select id="newznab_cat" multiple="multiple" style="min-width:10em;" ></select>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">${_('(select your Newznab categories on the left, and click the "update categories" button to use them for searching.) <b>don\'t forget to to save the form!')}</b></span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><input class="btn" type="button" class="newznab_cat_update" id="newznab_cat_update" value="${_('Update Categories')}" />
                                    <span class="updating_categories"></span>
                                </span>
                            </label>
                        </div>

                        <div id="newznab_add_div">
                            <input class="btn" type="button" class="newznab_save" id="newznab_add" value="${_('Add')}" />
                        </div>
                        <div id="newznab_update_div" style="display: none;">
                            <input class="btn btn-danger newznab_delete" type="button" class="newznab_delete" id="newznab_delete" value="${_('Delete')}" />
                        </div>
                    </div>

                    </fieldset>
                </div><!-- /component-group3 //-->
                % endif

                % if sickbeard.USE_TORRENTS:

                <div id="custom-torrent" class="component-group">

                <div class="component-group-desc">
                    <h3>${_('Configure Custom Torrent Providers')}</h3>
                    <p>${_('Add and setup or remove custom RSS providers.')}</p>
                </div>

                <fieldset class="component-group-list">
                    <div class="field-pair">
                        <label for="torrentrss_string">
                            <span class="component-title">${_('Select provider')}:</span>
                            <span class="component-desc">
                            <input type="hidden" name="torrentrss_string" id="torrentrss_string" />
                                <select id="editATorrentRssProvider" class="form-control input-sm">
                                    <option value="addTorrentRss">${_('-- add new provider --')}</option>
                                </select>
                            </span>
                        </label>
                    </div>

                    <div class="torrentRssProviderDiv" id="addTorrentRss">
                        <div class="field-pair">
                            <label for="torrentrss_name">
                                <span class="component-title">${_('Provider name')}:</span>
                                <input type="text" id="torrentrss_name" class="form-control input-sm input200" autocapitalize="off" />
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="torrentrss_url">
                                <span class="component-title">${_('RSS URL')}:</span>
                                <input type="text" id="torrentrss_url" class="form-control input-sm input350" autocapitalize="off" />
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="torrentrss_cookies">
                                <span class="component-title">${_('Cookies')}:</span>
                                <input type="text" id="torrentrss_cookies" class="form-control input-sm input350" autocapitalize="off" />
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">eg. uid=xx;pass=yy</span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="torrentrss_titleTAG">
                                <span class="component-title">${_('Search element')}:</span>
                                <input type="text" id="torrentrss_titleTAG" class="form-control input-sm input200" value="title" autocapitalize="off" />
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">${_('eg: title')}</span>
                            </label>
                        </div>
                        <div id="torrentrss_add_div">
                            <input type="button" class="btn torrentrss_save" id="torrentrss_add" value="${_('Add')}" />
                        </div>
                        <div id="torrentrss_update_div" style="display: none;">
                            <input type="button" class="btn btn-danger torrentrss_delete" id="torrentrss_delete" value="${_('Delete')}" />
                        </div>
                    </div>
                </fieldset>
            </div><!-- /component-group4 //-->
            % endif

            <br><input type="submit" class="btn config_submitter_refresh" value="${_('Save Changes')}" /><br>

            </div><!-- /config-components //-->

        </form>
    </div>
</div>
</%block>
