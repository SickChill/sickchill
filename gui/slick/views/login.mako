<%inherit file="/layouts/main.mako"/>
<%block name="content">
<div class="login">
    <form action="" method="post">
        <h1>SickRage</h1>
        <div class="ctrlHolder"><input class="inlay" name="username" type="text" placeholder="${_('Username')}" autocomplete="off" autocomplete="no" /></div>
        <div class="ctrlHolder"><input class="inlay" name="password" type="password" placeholder="${_('Password')}" autocomplete="off" /></div>
        <div class="ctrlHolder">
            <label class="remember_me" title="for 30 days"><input class="inlay" id="remember_me" name="remember_me" type="checkbox" value="1"checked="checked" /> ${_('Remember me')}</label>
            <input class="button" name="submit" type="submit" value="${_('Login')}" />
        </div>
    </form>
</div>
</%block>
