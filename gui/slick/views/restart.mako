<%inherit file="/layouts/main.mako"/>
<%block name="metas">
    <meta data-var="srDefaultPage" data-content="${sbDefaultPage}">
</%block>

<%block name="css">
    <style>
        .upgrade-notification {
            display: none;
        }
    </style>
</%block>

<%block name="content">
    <div class="row">
        <div class="col-md-12">
            <h2>${_('Performing Restart')}</h2>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div class="messages">
                <div id="shut_down_message">
                    ${_('Waiting for SickChill to shut down')}:
                    <span class="loading-spinner16" id="shut_down_loading"></span>
                    <span class="displayshow-icon-enable" id="shut_down_success" style="display: none;"></span>
                </div>

                <div id="restart_message" style="display: none;">
                    ${_('Waiting for SickChill to start again')}:
                    <span class="loading-spinner16" id="restart_loading"></span>
                    <span class="displayshow-icon-enable" id="restart_success" style="display: none;"></span>
                    <span class="displayshow-icon-disable" id="restart_failure" style="display: none;"></span>
                </div>

                <div id="refresh_message" style="display: none;">
                    ${_('Loading the default page')}:
                    <span class="loading-spinner16" id="refresh_loading"></span>
                </div>

                <div id="restart_fail_message" style="display: none;">
                    ${_('Error: The restart has timed out, perhaps something prevented SickChill from starting again?')}
                </div>
            </div>
        </div>
    </div>
</%block>
