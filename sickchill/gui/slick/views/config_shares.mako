<%inherit file="/layouts/config.mako"/>
<%!
     from sickchill import settings
%>
<%block name="pages">
    <form id="shares_form" action="save_shares" method="post">
        <div id="post-processing" class="component-group">
            <div class="row">
                <div class="col-xs-12">
                    <div class="component-group-desc">
                        <h3>${_('Windows Shares')}</h3>
                        <p>${_('Defines your existing windows shares so that we can add them to the browse dialog')}</p>
                    </div>
                </div>
            </div>
            <div class="row">
                % for i in range(0, len(settings.WINDOWS_SHARES) + 3):
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="form-group">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Share #{number}').format(number=i)}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <div class="col-md-2">
                                        <input type="text" name="share_name_${i}" id="share_name_${i}"/>
                                        <label for="share_name_${i}">${_('Share label')}</label>
                                    </div>
                                    <div class="col-md-2 col-md-offset-1">
                                        <input type="text" name="share_server_${i}" id="share_server_${i}"/>
                                        <label for="share_server_${i}">${_('Hostname or IP')}</label>
                                    </div>
                                    <div class="col-md-2 col-md-offset-1">
                                        <input type="text" name="share_path_${i}" id="share_path_${i}"/>
                                        <label for="share_path_${i}">${_('Share path')}</label>
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                % endfor
            </div>
        </div>
    </form>
</%block>
