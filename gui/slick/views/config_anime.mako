<%inherit file="/layouts/config.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>

<%block name="tabs">
	<li><a href="#animedb-settings">${_('AnimeDB Settings')}</a></li>
	<li><a href="#anime-look-feel">${_('Look &amp; Feel')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="saveAnime" method="post">

        <!-- /component-group //-->
        <div id="animedb-settings" class="tab-pane active component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-anime" title="AniDB"></span>
                        <h3><a href="${anon_url('http://anidb.info')}"
                               onclick="window.open(this.href, '_blank'); return false;">AniDB</a></h3>
                        <p>${_('AniDB is non-profit database of anime information that is freely open to the public')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <input type="checkbox" class="enabler" name="use_anidb"
                                       id="use_anidb" ${('', 'checked="checked"')[bool(sickbeard.USE_ANIDB)]} />
                                <label for="use_anidb" class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right">
                                <span class="component-desc">${_('Should SickRage use data from AniDB?')}</span>
                            </div>
                        </div>

                        <div id="content_use_anidb">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label for="anidb_username" class="component-title">${_('AniDB Username')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="anidb_username" id="anidb_username"
                                                   value="${sickbeard.ANIDB_USERNAME}"
                                                   class="form-control input-sm input350 pull-left" autocapitalize="off"
                                                   autocomplete="no" title="Username"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span class="component-desc">${_('Username of your AniDB account')}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label for="anidb_password" class="component-title">${_('AniDB Password')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="password" name="anidb_password" id="anidb_password"
                                                   value="${sickbeard.ANIDB_PASSWORD}"
                                                   class="form-control input-sm input350 pull-left" autocomplete="no"
                                                   autocapitalize="off" title="Password"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span class="component-desc">${_('Password of your AniDB account')}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <input type="checkbox" name="anidb_use_mylist"
                                           id="anidb_use_mylist" ${('', 'checked="checked"')[bool(sickbeard.ANIDB_USE_MYLIST)]}/>
                                    <label for="anidb_use_mylist" class="component-title">${_('AniDB MyList')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12">
                                    <span class="component-desc">${_('Do you want to add the PostProcessed Episodes to the MyList ?')}</span>
                                </div>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>
        </div>

        <!-- /component-group //-->
        <div id="anime-look-feel" class="tab-pane component-group">
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-look" title="look"></span>
                        <h3>${_('Look and Feel')}</h3>
                        <p>${_('How should the anime functions show and behave.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                <input type="checkbox" class="enabler" name="split_home"
                                       id="split_home" ${('', 'checked="checked"')[bool(sickbeard.ANIME_SPLIT_HOME)]} title="Splti"/>
                                <label for="split_home" class="component-title">${_('Split show lists')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right">
                                <span class="component-desc">${_('Separate anime and normal shows in groups')}</span>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>
        </div>
	</form>
</%block>
