<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill.oldbeard import classes
    import sickchill
%>
<%block name="content">
    <%
        if logLevel == sickchill.logger.WARNING:
            errors = classes.WarningViewer.errors
            title = _('WARNING logs')
        else:
            errors = classes.ErrorViewer.errors
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
