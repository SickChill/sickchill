<%inherit file="/layouts/config.mako"/>
<%!
    from sickbeard import subtitles
    import sickbeard
    from sickbeard.helpers import anon_url
%>

<%block name="scripts">
	<script>
		$(document).ready(function() {
			$("#subtitles_languages").tokenInput([${','.join("{\"id\": \"" + code + "\", name: \"" + subtitles.name_from_code(code) + "\"}" for code in subtitles.subtitle_code_filter())}], {
				method: "POST",
				hintText: _('Write to search a language and select it'),
				preventDuplicates: true,
				prePopulate: [${','.join("{\"id\": \"" + code + "\", name: \"" + subtitles.name_from_code(code) + "\"}" for code in subtitles.wanted_languages())}],
				resultsFormatter: function(item) {
					return "<li><img src='${srRoot}/images/subtitles/flags/" + item.id + ".png' onError='this.onerror=null;this.src=\"${srRoot}/images/flags/unknown.png\";' style='vertical-align: middle !important;' /> " + item.name + "</li>"
				},
				tokenFormatter: function(item) {
					return "<li><img src='${srRoot}/images/subtitles/flags/" + item.id + ".png' onError='this.onerror=null;this.src=\"${srRoot}/images/flags/unknown.png\";' style='vertical-align: middle !important;' /> " + item.name + "</li>"
				}
			});
		});
		$('#config-components').tabs();
		$('#subtitles_dir').fileBrowser({ title: _('Select Subtitles Download Directory') });
	</script>
</%block>

<%block name="tabs">
	<li><a href="#subtitles-search">${_('Subtitles Search')}</a></li>
	<li><a href="#subtitles-plugin">${_('Subtitles Plugin')}</a></li>
	<li><a href="#plugin-settings">${_('Plugin Settings')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="saveSubtitles" method="post">

	    <!-- /Search //-->
        <div id="subtitles-search">

	        <div class="row">
		        <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
			        <h3>${_('Subtitles Search')}</h3>
			        <p>${_('Settings that dictate how SickRage handles subtitles search results.')}</p>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <span class="component-title">${_('Search Subtitles')}</span>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox"
                                       class="enabler" ${('', ' checked="checked"')[bool(sickbeard.USE_SUBTITLES)]}
                                       id="use_subtitles" name="use_subtitles" title="Use Subtitles">
                            </div>
                        </div>

                        <div id="content_use_subtitles">

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Subtitle Languages')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <input type="text" id="subtitles_languages"
		                                   name="subtitles_languages"
		                                   autocapitalize="off"/>
	                            </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
	                                <span class="component-title">${_('Subtitle Directory')}</span>
                                </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
	                                        <input type="text" value="${sickbeard.SUBTITLES_DIR}" id="subtitles_dir"
	                                               name="subtitles_dir" class="form-control input-sm input300" title="Subtitle Directory">
                                        </div>
                                        <div class="clearfix"></div>
                                        <div class="col-md-12">
	                                        <span>${_('The directory where SickRage should store your <i>Subtitles</i> files.')}</span>
                                        </div>
                                        <div class="col-md-12">
	                                        <span><b>${_('Note')}:</b>&nbsp;${_('Leave empty if you want store subtitle in episode path.')}</span>
                                        </div>
                                    </div>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Subtitle Find Frequency')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <input type="number" name="subtitles_finder_frequency"
		                                   value="${sickbeard.SUBTITLES_FINDER_FREQUENCY}" hours="1" min="1"
		                                   step="1" class="form-control input-sm input75" title="Frequency"/>
		                            <label for="subtitles_finder_frequency">${_('time in hours between scans (default: 1)')}</label>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Perfect matches')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
	                                        <input type="checkbox"
	                                               class="enabler" ${('', ' checked="checked"')[bool(sickbeard.SUBTITLES_PERFECT_MATCH)]}
	                                               id="subtitles_perfect_match" name="subtitles_perfect_match">
	                                        <label for="subtitles_perfect_match">${_('Only download subtitles that match: release group, video codec, audio codec and resolution')}</label>
                                        </div>
                                    </div>
		                            <div class="row">
			                            <div class="col-md-12">
				                            <p>${_('If disabled you may get out of sync subtitles')}</p>
			                            </div>
		                            </div>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Subtitles History')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <input type="checkbox" name="subtitles_history"
		                                   id="subtitles_history" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_HISTORY)]}/>
		                            <label for="subtitles_history">${_('Log downloaded Subtitle on History page?')}</label>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Subtitles Multi-Language')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <div class="row">
			                            <div class="col-md-12">
				                            <input type="checkbox" name="subtitles_multi"
				                                   id="subtitles_multi" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_MULTI)]}/>
				                            <label for="subtitles_multi">${_('Append language codes to subtitle filenames?')}</label>
			                            </div>
		                            </div>
		                            <div class="row">
			                            <div class="col-md-12">
				                            <label><b>${_('Note')}:</b> ${_('This option is required if you use multiple subtitle languages.')}</label>
			                            </div>
		                            </div>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Delete unwanted subtitles')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <div class="row">
			                            <div class="col-md-12">
				                            <input type="checkbox" name="subtitles_keep_only_wanted"
				                                   id="subtitles_keep_only_wanted" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_KEEP_ONLY_WANTED)]}/>
				                            <label for="subtitles_keep_only_wanted">${_('Enable to delete unwanted subtitle languages bundled with release')}</label>
			                            </div>
		                            </div>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Embedded Subtitles')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <div class="row">
			                            <div class="col-md-12">
				                            <input type="checkbox" name="embedded_subtitles_all"
				                                   id="embedded_subtitles_all" ${('', 'checked="checked"')[bool(sickbeard.EMBEDDED_SUBTITLES_ALL)]}/>
				                            <label for="embedded_subtitles_all">${_('Ignore subtitles embedded inside video file?')}</label>
			                            </div>
		                            </div>
		                            <div class="row">
			                            <div class="col-md-12">
				                            <label><b>${_('Warning')}: </b>${_('this will ignore <u>all</u> embedded subtitles for every video file!')}</label>
			                            </div>
		                            </div>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Hearing Impaired Subtitles')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                            <input type="checkbox" name="subtitles_hearing_impaired"
		                                   id="subtitles_hearing_impaired" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_HEARING_IMPAIRED)]}/>
		                            <label for="subtitles_hearing_impaired">${_('Download hearing impaired style subtitles?')}</label>
	                            </div>
                            </div>

                            <div class="field-pair row">
	                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                            <span class="component-title">${_('Extra Scripts')}</span>
	                            </div>
	                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
	                                    <div class="col-md-12">
		                                    <input type="text" name="subtitles_extra_scripts"
		                                           value="${'|'.join(sickbeard.SUBTITLES_EXTRA_SCRIPTS)}"
		                                           class="form-control input-sm input350" autocapitalize="off"/>
	                                    </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
	                                        <ul>
		                                        <li>${_('See')} <a
				                                        href="https://github.com/SickRage/SickRage/wiki/Subtitle%20Scripts"><font
				                                        color='red'><b>Wiki</b></font></a> ${_('for a script arguments description.')}</li>
		                                        <li>${_('Additional scripts separated by <b>|</b>.')}</li>
		                                        <li>${_('Scripts are called after each episode has searched and downloaded subtitles.')}</li>
		                                        <li>${_('For any scripted languages, include the interpreter executable before the script. See the following example')}:</li>
                                                <ul>
                                                    <li>
                                                        ${_('For Windows:')}
                                                        <pre>C:\Python27\pythonw.exe C:\Script\test.py</pre>
                                                    </li>
                                                    <li>
                                                        ${_('For Linux / OS X:')}
                                                        <pre>python /Script/test.py</pre>
                                                    </li>
                                                </ul>
	                                        </ul>
                                        </div>
                                    </div>
	                            </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>
        </div>

	    <!-- /Plugin //-->
        <div id="subtitles-plugin">
	        <div class="row">
		        <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
			        <h3>${_('Subtitle Providers')}</h3>
			        <p>${_('Check off and drag the plugins into the order you want them to be used.')}</p>
			        <p class="note">${_('At least one plugin is required.')}</p>
			        <p class="note"><span style="font-size: 16px;">*</span>${_(' Web-scraping plugin')}</p>
		        </div>
		        <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
			        <fieldset class="component-group-list">

                        <div class="row">
                            <div class="col-md-12">
	                            <ul id="service_order_list">
                                    % for curService in sickbeard.subtitles.sorted_service_list():
			                            <li class="ui-state-default" id="${curService['name']}">
				                            <input type="checkbox" id="enable_${curService['name']}"
				                                   class="service_enabler" ${('', 'checked="checked"')[curService['enabled'] is True]}/>
				                            <a href="${anon_url(curService['url'])}" class="imgLink" target="_new">
					                            <img src="${srRoot}/images/subtitles/${curService['image']}"
					                                 alt="${curService['url']}" title="${curService['url']}" width="16"
					                                 height="16" style="vertical-align:middle;"/>
				                            </a>
				                            <span style="vertical-align:middle;">${curService['name'].capitalize()}</span>
				                            <span class="ui-icon ui-icon-arrowthick-2-n-s pull-right" style="vertical-align:middle;"></span>
			                            </li>
                                    % endfor
	                            </ul>
	                            <input type="hidden" name="service_order" id="service_order"
	                                   value="${' '.join(['%s:%d' % (x['name'], x['enabled']) for x in sickbeard.subtitles.sorted_service_list()])}"/>
                            </div>
                        </div>

			        </fieldset>
                </div>
            </div>
        </div>

        <!-- /Settings //-->
        <div id="plugin-settings">
            <div class="row">
	            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
		            <h3>${_('Provider Settings')}</h3>
		            <p>${_('Set user and password for each provider')}</p>
	            </div>
	            <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
		            <fieldset class="component-group-list">
                        <%
                            providerLoginDict = {
                                'legendastv': {'user': sickbeard.LEGENDASTV_USER, 'pass': sickbeard.LEGENDASTV_PASS},
                                'addic7ed': {'user': sickbeard.ADDIC7ED_USER, 'pass': sickbeard.ADDIC7ED_PASS},
                                ## 'itasa': {'user': sickbeard.ITASA_USER, 'pass': sickbeard.ITASA_PASS},
                                'opensubtitles': {'user': sickbeard.OPENSUBTITLES_USER, 'pass': sickbeard.OPENSUBTITLES_PASS}
                            }
                        %>
                        % for curService in sickbeard.subtitles.sorted_service_list():
                            <%
                                if curService['name'] not in providerLoginDict.keys():
                                    continue
                            %>
				            <div class="field-pair row">
					            <div class="col-lg-6 col-md-6 col-sm-12 col-xs-12">
                                    <div class="row">
                                        <div class="col-md-12">
	                                        <span class="component-title">${curService['name'].capitalize()} ${_('User Name')}</span>
                                        </div>
                                    </div>
						            <div class="row">
							            <div class="col-md-12">
								            <input type="text" name="${curService['name']}_user"
								                   id="${curService['name']}_user"
								                   value="${providerLoginDict[curService['name']]['user']}"
								                   class="form-control input-sm input300" autocapitalize="off"
								                   autocomplete="no" title="Username"/>
							            </div>
						            </div>
					            </div>
					            <div class="col-lg-6 col-md-6 col-sm-12 col-xs-12">
						            <div class="row">
							            <div class="col-md-12">
								            <span class="component-title">${curService['name'].capitalize()} ${_('Password')}</span>
							            </div>
						            </div>
						            <div class="row">
							            <div class="col-md-12">
								            <input type="password" name="${curService['name']}_pass"
								                   id="${curService['name']}_pass"
								                   value="${providerLoginDict[curService['name']]['pass']}"
								                   class="form-control input-sm input300" autocomplete="no"
								                   autocapitalize="off" title="Password"/>
							            </div>
						            </div>
					            </div>
				            </div>
                        % endfor
		            </fieldset>
	            </div>
            </div>
        </div>

    </form>
</%block>
