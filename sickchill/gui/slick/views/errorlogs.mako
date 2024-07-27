<%inherit file="/layouts/main.mako" />
<%!
    from sickchill.logging.weblog import WebErrorViewer
    import logging
%>
<%block name="content">
    <%
        if logLevel == logging.WARNING:
            errors = WebErrorViewer.warnings
            title = _('WARNING logs')
        else:
            errors = WebErrorViewer.errors
            title = _('ERROR logs')
    %>
    <div class="row">
        <div class="col-md-12">
            <h1 class="header">${title}</h1>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12 align-left">
            <pre>
                % if errors:
                    % for curError in sorted(errors, key=lambda error: error.time, reverse=True)[:500]:
                        ${curError.time} ${curError.message}
                    % endfor
                % else:
                    ${_('There are no events to display.')}
                % endif
            </pre>
        </div>
    </div>
</%block>
