<%inherit file="/layouts/main.mako"/>
<%block name="content">
    <h1 class="header">${header}</h1>
    <div class="col-lg-12 text-center">
      <div class="row h1">
        ${_('You have reached this page by accident, please check the url.')}
      </div>
      <div class="row h1">
        <a href="${reverse_url("home", "")}"><i class="fa fa-fw fa-home text-center big"></i>&nbsp;${_('Home')}</a>
      </div>
    </div>
</%block>
