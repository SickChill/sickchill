<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill.oldbeard.helpers import is_ip_local
    from sickchill import oldbeard, logger, settings
%>
<%block name="content">
    <div class="row">
        % if not (is_ip_local(remote_ip) or (settings.WEB_PASSWORD and settings.WEB_USERNAME)):
            <% logger.warning('Remote access was attempted by {}'.format(remote_ip)) %>
            <div class="nicetry col-md-10">
                <div class="row">
                    <div class="col-md-12">
                        <h1>SickChill</h1>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <p>
                            If you are the owner of this server, your SickChill installation is exposed to the internet without a password.
                            You will need access to the local network where this machine is to set the password through the interface.
                            Otherwise, you will need to stop SickChill and edit web_user and web_pass in the config.ini manually before
                            starting SickChill back up.

                            This may seem like an inconvenience, but your logins and file system being exposed is much more inconvenient.
                        </p>
                        <p>
                            Your IP: ${remote_ip}
                        </p>
                        <p>
                            If you are an attacker, the party is over.
                        </p>
                    </div>
                </div>
            </div>
        % else:
            <div class="col-lg-4 col-lg-offset-4 col-md-6 col-md-offset-3 col-sm-8 col-sm-offset-2">
                <div class="login">
                    <form action="" method="post">
                        <div class="row">
                            <div class="col-md-12">
                                <h1>SickChill</h1>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    <label for="username">${_('Username')}</label>
                                    <input class="form-control" title="${_('Username')}" name="username" type="text"
                                           placeholder="${_('Username')}" autocomplete="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    <label for="password">${_('Password')}</label>
                                    <input class="form-control" title="${_('Password')}" name="password" type="password"
                                           placeholder="${_('Password')}" autocomplete="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    <label class="remember_me" title="${_('for 30 days')}">
                                        <input class="inlay" id="remember_me" name="remember_me" type="checkbox" value="1" checked="checked"/>&nbsp;${_('Remember me')}
                                    </label>
                                    <input class="btn btn-default pull-right" name="submit" type="submit" value="${_('Login')}"/>
                                </div>
                            </div>
                        </div>
                        %if login_error:
                        <div class="row">
                            <div class="col-md-12 text-center text-danger">
                                <i class="glyphicon glyphicon-alert" title="${login_error}"></i>
                                &nbsp;${login_error}
                            </div>
                        </div>
                        %endif
                    </form>
                </div>
            </div>
        % endif
    </div>
</%block>
