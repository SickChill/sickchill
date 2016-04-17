<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
    from sickrage.providers.GenericProvider import GenericProvider
%>
<%block name="scripts">
	<script type="text/javascript" src="${srRoot}/js/configProviders.js"></script>
	<script type="text/javascript">
		$(document).ready(function() {
            % if sickbeard.USE_NZBS:
				var show_nzb_providers = ${("false", "true")[bool(sickbeard.USE_NZBS)]};
                % for curNewznabProvider in sickbeard.newznabProviderList:
                    $(this).addProvider('${curNewznabProvider.get_id()}', '${curNewznabProvider.name}', '${curNewznabProvider.url}', '${curNewznabProvider.key}', '${curNewznabProvider.catIDs}', ${int(curNewznabProvider.default)}, show_nzb_providers);
                % endfor
            % endif
            % if sickbeard.USE_TORRENTS:
                % for curTorrentRssProvider in sickbeard.torrentRssProviderList:
					$(this).addTorrentRssProvider('${curTorrentRssProvider.get_id()}', '${curTorrentRssProvider.name}', '${curTorrentRssProvider.url}', '${curTorrentRssProvider.cookies}', '${curTorrentRssProvider.titleTAG}');
                % endfor
            % endif
		});
		$('#config-components').tabs();
	</script>
</%block>
<%block name="content">
	<div id="config">
		<div id="config-content">
            % if not header is UNDEFINED:
				<h1 class="header">${header}</h1>
            % else:
				<h1 class="title">${title}</h1>
            % endif

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
								<blockquote style="margin: 20px 0;">NZB/${_('Torrent providers can be toggled in ')}
									<b><a href="${srRoot}/config/search">Search Settings</a></b></blockquote>
                            % else:
								<br>
                            % endif

							<div>
								<p class="note"><span
										class="red-text">*</span> ${_('Provider does not support backlog searches at this time.')}
								</p>
								<p class="note"><span class="red-text">!</span> ${_('Provider is <b>NOT WORKING</b>.')}
								</p>
							</div>
						</div>

						<fieldset class="component-group-list">
							<ul id="provider_order_list">
                                % for curProvider in sickbeard.providers.sortedProviderList():
                                <%
                                    ## These will show the '!' not saying they are broken
                                    broken_providers = {}
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
									<li class="ui-state-default ${('nzb-provider', 'torrent-provider')[bool(curProvider.provider_type == GenericProvider.TORRENT)]}"
									    id="${curName}">
										<input type="checkbox" id="enable_${curName}"
										       class="provider_enabler" ${('', 'checked="checked"')[curProvider.is_enabled() is True]}/>
										<a href="${anon_url(curURL)}" class="imgLink" rel="noreferrer"
										   onclick="window.open(this.href, '_blank'); return false;"><img
												src="${srRoot}/images/providers/${curProvider.image_name()}"
												alt="${curProvider.name}" title="${curProvider.name}" width="16"
												height="16" style="vertical-align:middle;"/></a>
										<span style="vertical-align:middle;">${curProvider.name}</span>
                                        ${('<span class="red-text">*</span>', '')[bool(curProvider.supports_backlog)]}
                                        ${('<span class="red-text">!</span>', '')[bool(curProvider.get_id() not in broken_providers)]}
										<span class="ui-icon ui-icon-arrowthick-2-n-s pull-right"
										      style="vertical-align:middle;"></span>
										<span class="ui-icon ${('ui-icon-locked','ui-icon-unlocked')[bool(curProvider.public)]} pull-right"
										      style="vertical-align:middle;"></span>
									</li>
                                % endfor
							</ul>
							<input type="hidden" name="provider_order" id="provider_order"
							       value="${" ".join([x.get_id()+':'+str(int(x.is_enabled())) for x in sickbeard.providers.sortedProviderList()])}"/>
							<br><input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/><br>
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
                                        for curProvider in sickbeard.providers.sortedProviderList():
                                            if curProvider.provider_type == GenericProvider.NZB and (not sickbeard.USE_NZBS or not curProvider.is_enabled()):
                                                continue
                                            elif curProvider.provider_type == GenericProvider.TORRENT and ( not sickbeard.USE_TORRENTS or not curProvider.is_enabled()):
                                                continue
                                            provider_config_list.append(curProvider)
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
                            % for curNewznabProvider in [curProvider for curProvider in sickbeard.newznabProviderList]:
								<div class="providerDiv" id="${curNewznabProvider.get_id()}Div">
                                    % if curNewznabProvider.default and curNewznabProvider.needs_auth:
										<div class="field-pair">
											<label for="${curNewznabProvider.get_id()}_url">
												<span class="component-title">${_('URL')}:</span>
                                <span class="component-desc">
                                    <input type="text" id="${curNewznabProvider.get_id()}_url"
                                           value="${curNewznabProvider.url}" class="form-control input-sm input350"
                                           disabled autocapitalize="off"/>
                                </span>
											</label>
										</div>
										<div class="field-pair">
											<label for="${curNewznabProvider.get_id()}_hash">
												<span class="component-title">${_('API key')}:</span>
                                <span class="component-desc">
                                    <input type="text" id="${curNewznabProvider.get_id()}_hash"
                                           value="${curNewznabProvider.key}"
                                           newznab_name="${curNewznabProvider.get_id()}_hash"
                                           class="newznab_key form-control input-sm input350" autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNewznabProvider, 'enable_daily'):
										<div class="field-pair">
											<label for="${curNewznabProvider.get_id()}_enable_daily">
												<span class="component-title">${_('Enable daily searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curNewznabProvider.get_id()}_enable_daily"
                                           id="${curNewznabProvider.get_id()}_enable_daily" ${('', 'checked="checked"')[bool(curNewznabProvider.enable_daily)]}/>
                                    <p>${_('enable provider to perform daily searches.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNewznabProvider, 'enable_backlog'):
										<div class="field-pair${(' hidden', '')[curNewznabProvider.supports_backlog]}">
											<label for="${curNewznabProvider.get_id()}_enable_backlog">
												<span class="component-title">${_('Enable backlog searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curNewznabProvider.get_id()}_enable_backlog"
                                           id="${curNewznabProvider.get_id()}_enable_backlog" ${('', 'checked="checked"')[bool(curNewznabProvider.enable_backlog and curNewznabProvider.supports_backlog)]}/>
                                    <p>${_('enable provider to perform backlog searches.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNewznabProvider, 'search_mode'):
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
                                    <input type="radio" name="${curNewznabProvider.get_id()}_search_mode"
                                           id="${curNewznabProvider.get_id()}_search_mode_sponly"
                                           value="sponly" ${('', 'checked="checked"')[curNewznabProvider.search_mode=="sponly"]}/>${_('season packs only.')}
                                </span>
											</label>
											<label>
												<span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${curNewznabProvider.get_id()}_search_mode"
                                           id="${curNewznabProvider.get_id()}_search_mode_eponly"
                                           value="eponly" ${('', 'checked="checked"')[curNewznabProvider.search_mode=="eponly"]}/>${_('episodes only.')}
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNewznabProvider, 'search_fallback'):
										<div class="field-pair">
											<label for="${curNewznabProvider.get_id()}_search_fallback">
												<span class="component-title">${_('Enable fallback')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curNewznabProvider.get_id()}_search_fallback"
                                           id="${curNewznabProvider.get_id()}_search_fallback" ${('', 'checked="checked"')[bool(curNewznabProvider.search_fallback)]}/>
                                    <p>${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

								</div>
                            % endfor

                            % for curNzbProvider in [curProvider for curProvider in sickbeard.providers.sortedProviderList() if curProvider.provider_type == GenericProvider.NZB and curProvider not in sickbeard.newznabProviderList]:
								<div class="providerDiv" id="${curNzbProvider.get_id()}Div">
                                    % if hasattr(curNzbProvider, 'username'):
										<div class="field-pair">
											<label for="${curNzbProvider.get_id()}_username">
												<span class="component-title">${_('Username')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curNzbProvider.get_id()}_username"
                                           value="${curNzbProvider.username}" class="form-control input-sm input350"
                                           autocapitalize="off" autocomplete="no"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNzbProvider, 'api_key'):
										<div class="field-pair">
											<label for="${curNzbProvider.get_id()}_api_key">
												<span class="component-title">${_('API key')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curNzbProvider.get_id()}_api_key"
                                           value="${curNzbProvider.api_key}" class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif


                                    % if hasattr(curNzbProvider, 'enable_daily'):
										<div class="field-pair">
											<label for="${curNzbProvider.get_id()}_enable_daily">
												<span class="component-title">${_('Enable daily searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curNzbProvider.get_id()}_enable_daily"
                                           id="${curNzbProvider.get_id()}_enable_daily" ${('', 'checked="checked"')[bool(curNzbProvider.enable_daily)]}/>
                                    <p>${_('enable provider to perform daily searches.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNzbProvider, 'enable_backlog'):
										<div class="field-pair${(' hidden', '')[curNzbProvider.supports_backlog]}">
											<label for="${curNzbProvider.get_id()}_enable_backlog">
												<span class="component-title">${_('Enable backlog searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curNzbProvider.get_id()}_enable_backlog"
                                           id="${curNzbProvider.get_id()}_enable_backlog" ${('', 'checked="checked"')[bool(curNzbProvider.enable_backlog and curNzbProvider.supports_backlog)]}/>
                                    <p>${_('enable provider to perform backlog searches.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNzbProvider, 'search_mode'):
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
                                    <input type="radio" name="${curNzbProvider.get_id()}_search_mode"
                                           id="${curNzbProvider.get_id()}_search_mode_sponly"
                                           value="sponly" ${('', 'checked="checked"')[curNzbProvider.search_mode=="sponly"]}/>season packs only.
                                </span>
											</label>
											<label>
												<span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${curNzbProvider.get_id()}_search_mode"
                                           id="${curNzbProvider.get_id()}_search_mode_eponly"
                                           value="eponly" ${('', 'checked="checked"')[curNzbProvider.search_mode=="eponly"]}/>episodes only.
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curNzbProvider, 'search_fallback'):
										<div class="field-pair">
											<label for="${curNzbProvider.get_id()}_search_fallback">
												<span class="component-title">${_('Enable fallback')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curNzbProvider.get_id()}_search_fallback"
                                           id="${curNzbProvider.get_id()}_search_fallback" ${('', 'checked="checked"')[bool(curNzbProvider.search_fallback)]}/>
                                    <p>${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

								</div>
                            % endfor

                            % for curTorrentProvider in [curProvider for curProvider in sickbeard.providers.sortedProviderList() if curProvider.provider_type == GenericProvider.TORRENT]:
								<div class="providerDiv" id="${curTorrentProvider.get_id()}Div">

                                    % if hasattr(curTorrentProvider, 'custom_url'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_custom_url">
												<span class="component-title">${_('Custom URL')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curTorrentProvider.get_id()}_custom_url"
                                           id="${curTorrentProvider.get_id()}_custom_url"
                                           value="${curTorrentProvider.custom_url}"
                                           class="form-control input-sm input350" autocapitalize="off"/>
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

                                    % if hasattr(curTorrentProvider, 'api_key'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_api_key">
												<span class="component-title">${_('Api key')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curTorrentProvider.get_id()}_api_key"
                                           id="${curTorrentProvider.get_id()}_api_key"
                                           value="${curTorrentProvider.api_key}" class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'digest'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_digest">
												<span class="component-title">${_('Digest')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curTorrentProvider.get_id()}_digest"
                                           id="${curTorrentProvider.get_id()}_digest"
                                           value="${curTorrentProvider.digest}" class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'hash'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_hash">
												<span class="component-title">${_('Hash')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curTorrentProvider.get_id()}_hash"
                                           id="${curTorrentProvider.get_id()}_hash" value="${curTorrentProvider.hash}"
                                           class="form-control input-sm input350" autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'username'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_username">
												<span class="component-title">${_('Username')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curTorrentProvider.get_id()}_username"
                                           id="${curTorrentProvider.get_id()}_username"
                                           value="${curTorrentProvider.username}" class="form-control input-sm input350"
                                           autocapitalize="off" autocomplete="no"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'password'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_password">
												<span class="component-title">${_('Password')}:</span>
                                <span class="component-desc">
                                    <input type="password" name="${curTorrentProvider.get_id()}_password"
                                           id="${curTorrentProvider.get_id()}_password"
                                           value="${curTorrentProvider.password}" class="form-control input-sm input350"
                                           autocomplete="no" autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'passkey'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_passkey">
												<span class="component-title">${_('Passkey')}:</span>
                                <span class="component-desc">
                                    <input type="text" name="${curTorrentProvider.get_id()}_passkey"
                                           id="${curTorrentProvider.get_id()}_passkey"
                                           value="${curTorrentProvider.passkey}" class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'pin'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_pin">
												<span class="component-title">${_('Pin')}:</span>
                                <span class="component-desc">
                                    <input type="password" name="${curTorrentProvider.get_id()}_pin"
                                           id="${curTorrentProvider.get_id()}_pin" value="${curTorrentProvider.pin}"
                                           class="form-control input-sm input100" autocomplete="no"
                                           autocapitalize="off"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'ratio'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_ratio">
												<span class="component-title"
												      id="${curTorrentProvider.get_id()}_ratio_desc">${_('Seed ratio')}
													:</span>
                                <span class="component-desc">
                                    <input type="number" min="-1" step="0.1" name="${curTorrentProvider.get_id()}_ratio"
                                           id="${curTorrentProvider.get_id()}_ratio" value="${curTorrentProvider.ratio}"
                                           class="form-control input-sm input75"/>
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

                                    % if hasattr(curTorrentProvider, 'minseed'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_minseed">
												<span class="component-title"
												      id="${curTorrentProvider.get_id()}_minseed_desc">${_('Minimum seeders')}
													:</span>
                                <span class="component-desc">
                                    <input type="number" min="0" step="1" name="${curTorrentProvider.get_id()}_minseed"
                                           id="${curTorrentProvider.get_id()}_minseed"
                                           value="${curTorrentProvider.minseed}" class="form-control input-sm input75"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'minleech'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_minleech">
												<span class="component-title"
												      id="${curTorrentProvider.get_id()}_minleech_desc">${_('Minimum leechers')}
													:</span>
                                <span class="component-desc">
                                    <input type="number" min="0" step="1" name="${curTorrentProvider.get_id()}_minleech"
                                           id="${curTorrentProvider.get_id()}_minleech"
                                           value="${curTorrentProvider.minleech}"
                                           class="form-control input-sm input75"/>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'confirmed'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_confirmed">
												<span class="component-title">${_('Confirmed download')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_confirmed"
                                           id="${curTorrentProvider.get_id()}_confirmed" ${('', 'checked="checked"')[bool(curTorrentProvider.confirmed)]}/>
                                    <p>${_('only download torrents from trusted or verified uploaders ?')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'ranked'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_ranked">
												<span class="component-title">${_('Ranked torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_ranked"
                                           id="${curTorrentProvider.get_id()}_ranked" ${('', 'checked="checked"')[bool(curTorrentProvider.ranked)]} />
                                    <p>${_('only download ranked torrents (trusted releases)')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'engrelease'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_engrelease">
												<span class="component-title">${_('English torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_engrelease"
                                           id="${curTorrentProvider.get_id()}_engrelease" ${('', 'checked="checked"')[bool(curTorrentProvider.engrelease)]} />
                                    <p>${_('only download english torrents, or torrents containing english subtitles')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'onlyspasearch'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_onlyspasearch">
												<span class="component-title">${_('For Spanish torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_onlyspasearch"
                                           id="${curTorrentProvider.get_id()}_onlyspasearch" ${('', 'checked="checked"')[bool(curTorrentProvider.onlyspasearch)]} />
                                    <p>${_('ONLY search on this provider if show info is defined as "Spanish" (avoid provider\'s use for VOS shows)')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'sorting'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_sorting">
												<span class="component-title">${_('Sorting results by')}</span>
                                <span class="component-desc">
                                    <select name="${curTorrentProvider.get_id()}_sorting"
                                            id="${curTorrentProvider.get_id()}_sorting" class="form-control input-sm">
                                        % for curAction in ('last', 'seeders', 'leechers'):
		                                    <option value="${curAction}" ${('', 'selected="selected"')[curAction == curTorrentProvider.sorting]}>${curAction}</option>
                                        % endfor
                                    </select>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'freeleech'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_freeleech">
												<span class="component-title">${_('Freeleech')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_freeleech"
                                           id="${curTorrentProvider.get_id()}_freeleech" ${('', 'checked="checked"')[bool(curTorrentProvider.freeleech)]}/>
                                    <p>${_('only download <b>"FreeLeech"</b> torrents.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'enable_daily'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_enable_daily">
												<span class="component-title">${_('Enable daily searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_enable_daily"
                                           id="${curTorrentProvider.get_id()}_enable_daily" ${('', 'checked="checked"')[bool(curTorrentProvider.enable_daily)]}/>
                                    <p>${_('enable provider to perform daily searches.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'enable_backlog'):
										<div class="field-pair${(' hidden', '')[curTorrentProvider.supports_backlog]}">
											<label for="${curTorrentProvider.get_id()}_enable_backlog">
												<span class="component-title">${_('Enable backlog searches')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_enable_backlog"
                                           id="${curTorrentProvider.get_id()}_enable_backlog" ${('', 'checked="checked"')[bool(curTorrentProvider.enable_backlog and curTorrentProvider.supports_backlog)]}/>
                                    <p>${_('enable provider to perform backlog searches.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'search_mode'):
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
                                    <input type="radio" name="${curTorrentProvider.get_id()}_search_mode"
                                           id="${curTorrentProvider.get_id()}_search_mode_sponly"
                                           value="sponly" ${('', 'checked="checked"')[curTorrentProvider.search_mode=="sponly"]}/>season packs only.
                                </span>
											</label>
											<label>
												<span class="component-title"></span>
                                <span class="component-desc">
                                    <input type="radio" name="${curTorrentProvider.get_id()}_search_mode"
                                           id="${curTorrentProvider.get_id()}_search_mode_eponly"
                                           value="eponly" ${('', 'checked="checked"')[curTorrentProvider.search_mode=="eponly"]}/>episodes only.
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'search_fallback'):
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_search_fallback">
												<span class="component-title">${_('Enable fallback')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_search_fallback"
                                           id="${curTorrentProvider.get_id()}_search_fallback" ${('', 'checked="checked"')[bool(curTorrentProvider.search_fallback)]}/>
                                    <p>${_('when searching for a complete season depending on search mode you may return no results, this helps by restarting the search using the opposite search mode.')}</p>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'cat') and curTorrentProvider.get_id() == 'tntvillage':
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_cat">
												<span class="component-title">${_('Category')}:</span>
                                <span class="component-desc">
                                    <select name="${curTorrentProvider.get_id()}_cat"
                                            id="${curTorrentProvider.get_id()}_cat" class="form-control input-sm">
                                        % for i in curTorrentProvider.category_dict.keys():
		                                    <option value="${curTorrentProvider.category_dict[i]}" ${('', 'selected="selected"')[curTorrentProvider.category_dict[i] == curTorrentProvider.cat]}>${i}</option>
                                        % endfor
                                    </select>
                                </span>
											</label>
										</div>
                                    % endif

                                    % if hasattr(curTorrentProvider, 'subtitle') and curTorrentProvider.get_id() == 'tntvillage':
										<div class="field-pair">
											<label for="${curTorrentProvider.get_id()}_subtitle">
												<span class="component-title">${_('Subtitled')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="${curTorrentProvider.get_id()}_subtitle"
                                           id="${curTorrentProvider.get_id()}_subtitle" ${('', 'checked="checked"')[bool(curTorrentProvider.subtitle)]}/>
                                    <p>${_('select torrent with Italian subtitle')}</p>
                                </span>
											</label>
										</div>
                                    % endif

								</div>
                            % endfor


							<!-- end div for editing providers -->

							<input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/><br>

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
                                    <input type="hidden" name="newznab_string" id="newznab_string"/>
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
											<input type="text" id="newznab_name" class="form-control input-sm input200"
											       autocapitalize="off"/>
										</label>
									</div>
									<div class="field-pair">
										<label for="newznab_url">
											<span class="component-title">${_('Site URL')}:</span>
											<input type="text" id="newznab_url" class="form-control input-sm input350"
											       autocapitalize="off"/>
										</label>
									</div>
									<div class="field-pair">
										<label for="newznab_key">
											<span class="component-title">${_('API key')}:</span>
											<input type="password" id="newznab_key"
											       class="form-control input-sm input350" autocapitalize="off"/>
										</label>
										<label>
											<span class="component-title">&nbsp;</span>
											<span class="component-desc">(if not required, type 0)</span>
										</label>
									</div>

									<div class="field-pair" id="newznabcapdiv">
										<label>
											<span class="component-title">${_('Newznab search categories')}:</span>
											<select id="newznab_cap" multiple="multiple"
											        style="min-width:10em;"></select>
											<select id="newznab_cat" multiple="multiple"
											        style="min-width:10em;"></select>
										</label>
										<label>
											<span class="component-title">&nbsp;</span>
											<span class="component-desc"><b>${_('select your Newznab categories on the left, and click the "update categories" button to use them for searching.) <b>don\'t forget to to save the form!')}</b></span>
										</label>
										<label>
											<span class="component-title">&nbsp;</span>
                                <span class="component-desc"><input class="btn" type="button" class="newznab_cat_update"
                                                                    id="newznab_cat_update"
                                                                    value="${_('Update Categories')}"/>
                                    <span class="updating_categories"></span>
                                </span>
										</label>
									</div>

									<div id="newznab_add_div">
										<input class="btn" type="button" class="newznab_save" id="newznab_add"
										       value="${_('Add')}"/>
									</div>
									<div id="newznab_update_div" style="display: none;">
										<input class="btn btn-danger newznab_delete" type="button"
										       class="newznab_delete" id="newznab_delete" value="${_('Delete')}"/>
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
                            <input type="hidden" name="torrentrss_string" id="torrentrss_string"/>
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
											<input type="text" id="torrentrss_name"
											       class="form-control input-sm input200" autocapitalize="off"/>
										</label>
									</div>
									<div class="field-pair">
										<label for="torrentrss_url">
											<span class="component-title">${_('RSS URL')}:</span>
											<input type="text" id="torrentrss_url"
											       class="form-control input-sm input350" autocapitalize="off"/>
										</label>
									</div>
									<div class="field-pair">
										<label for="torrentrss_cookies">
											<span class="component-title">${_('Cookies')}:</span>
											<input type="text" id="torrentrss_cookies"
											       class="form-control input-sm input350" autocapitalize="off"/>
										</label>
										<label>
											<span class="component-title">&nbsp;</span>
											<span class="component-desc">eg. uid=xx;pass=yy</span>
										</label>
									</div>
									<div class="field-pair">
										<label for="torrentrss_titleTAG">
											<span class="component-title">${_('Search element')}:</span>
											<input type="text" id="torrentrss_titleTAG"
											       class="form-control input-sm input200" value="title"
											       autocapitalize="off"/>
										</label>
										<label>
											<span class="component-title">&nbsp;</span>
											<span class="component-desc">${_('eg: title')}</span>
										</label>
									</div>
									<div id="torrentrss_add_div">
										<input type="button" class="btn torrentrss_save" id="torrentrss_add"
										       value="${_('Add')}"/>
									</div>
									<div id="torrentrss_update_div" style="display: none;">
										<input type="button" class="btn btn-danger torrentrss_delete"
										       id="torrentrss_delete" value="${_('Delete')}"/>
									</div>
								</div>
							</fieldset>
						</div><!-- /component-group4 //-->
                    % endif

					<br><input type="submit" class="btn config_submitter_refresh" value="${_('Save Changes')}"/><br>

				</div><!-- /config-components //-->

			</form>
		</div>
	</div>
</%block>
