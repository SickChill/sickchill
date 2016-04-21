<%inherit file="/layouts/main.mako"/>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
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
            ${info_download_station}
            <iframe id="extFrame" src="${webui_url}" style="width:100%;height:500px;border: 1px black solid;" frameBorder="0"></iframe>
        </div>
    </div>
</%block>
