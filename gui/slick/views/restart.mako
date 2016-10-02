<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
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
        <%
            try:
                themeSpinner = sbThemeName
            except NameError:
                themeSpinner = sickbeard.THEME_NAME
        %>
        <div class="col-md-12">
            <div class="messages">
                <div id="shut_down_message">
                    ${_('Waiting for SickRage to shut down')}:
                    <img src="${srRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16"
                         id="shut_down_loading"/>
                    <img src="${srRoot}/images/yes16.png" height="16" width="16" id="shut_down_success"
                         style="display: none;"/>
                </div>

                <div id="restart_message" style="display: none;">
                    ${_('Waiting for SickRage to start again')}:
                    <img src="${srRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="restart_loading"/>
                    <img src="${srRoot}/images/yes16.png" height="16" width="16" id="restart_success"
                         style="display: none;"/>
                    <img src="${srRoot}/images/no16.png" height="16" width="16" id="restart_failure"
                         style="display: none;"/>
                </div>

                <div id="refresh_message" style="display: none;">
                    ${_('Loading the default page')}:
                    <img src="${srRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="refresh_loading"/>
                </div>

                <div id="restart_fail_message" style="display: none;">
                    ${_('Error: The restart has timed out, perhaps something prevented SickRage from starting again?')}
                </div>
            </div>
        </div>
    </div>
</%block>
