<%inherit file="main.mako"/>
<%!
    import os
    import datetime
    import sickbeard
    from sickbeard.common import SKIPPED, ARCHIVED, IGNORED, statusStrings, cpu_presets
    from sickbeard.sbdatetime import sbdatetime, date_presets, time_presets
    from sickbeard.helpers import anon_url
%>

<%block name="scripts">
	<script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
</%block>
<%block name="content">
	<div class="row">
		<div class="col-md-12">
            % if not header is UNDEFINED:
				<h1 class="header">${header}</h1>
            % else:
				<h1 class="title">${title}</h1>
            % endif
		</div>
	</div>
	<div class="row">
		<div class="col-md-12">
			<div class="row">
				<div class="col-md-12">
					<div id="config-components">
						<ul>
                            <%block name="tabs"/>
						</ul>
						<div id="config">
							<div id="config-components">
                                <%block name="pages"/>
							</div>
						</div>
					</div>
				</div>
			</div>
			<br/>
			<div class="row">
				<div class="col-lg-10 col-md-10 col-sm-10 col-xs-12 pull-right">
					<h6 class="pull-right">
						<b>
							<span class="path pull-right">${sickbeard.DATA_DIR}</span>
							<span>${_('All non-absolute folder locations are relative to ')}</span>
						</b>
					</h6>
				</div>
				<div class="col-lg-2 col-md-2 col-sm-2 col-xs-12">
					<input type="button" onclick="$('#configForm').submit()" class="btn pull-left config_submitter button" value="${_('Save Changes')}"/>
				</div>
			</div>
		</div>
	</div>
</%block>

