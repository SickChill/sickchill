<%inherit file="/layouts/main.mako"/>
<%block name="content">
    <div class="login">
        <form action="" method="post">
            <div class="row">
                <div class="col-md-12">
                    <h1>SickRage</h1>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input class="form-control" title="username" name="username" type="text" placeholder="${_('Username')}" autocomplete="off" />
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input class="form-control" title="password" name="password" type="password" placeholder="${_('Password')}" autocomplete="off" />
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="form-group">
                        <label class="remember_me" title="for 30 days"><input class="inlay" id="remember_me" name="remember_me" type="checkbox" value="1" checked="checked" /> ${_('Remember me')}</label>
                        <input class="btn btn-default pull-right" name="submit" type="submit" value="${_('Login')}" />
                    </div>
                </div>
            </div>
        </form>
    </div>
</%block>
