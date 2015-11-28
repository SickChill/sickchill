<%inherit file="/layouts/main.mako"/>
<%block name="content">
<div class="login">
    <form action="" method="post">
        <h1>SickRage</h1>
        <div class="ctrlHolder"><input class="inlay" name="username" type="text" placeholder="Username" autocomplete="off"  autocapitalize="off" /></div>
        <div class="ctrlHolder"><input class="inlay" name="password" type="password" placeholder="Password" autocomplete="off"  autocapitalize="off" /></div>
        <div class="ctrlHolder">
            <label class="remember_me" title="for 30 days"><input class="inlay" id="remember_me" name="remember_me" type="checkbox" value="1"checked="checked"  autocapitalize="off" /> Remember me</label>
            <input class="button" name="submit" type="submit" value="Login"  autocapitalize="off" />
        </div>
    </form>
</div>
</%block>
