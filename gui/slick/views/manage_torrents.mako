<%inherit file="/layouts/main.mako"/>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
</%block>
<%block name="content">
    <div class="container-fluid">
        % if not header is UNDEFINED:
		    <h1 class="header">${header}</h1>
        % else:
		    <h1 class="title">${title}</h1>
        % endif

        ${info_download_station}
	    <iframe id="extFrame" src="${webui_url}" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
    </div>
</%block>
