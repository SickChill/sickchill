<%inherit file="/layouts/config.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard.filters import hide
    from sickchill.oldbeard.helpers import anon_url
%>

<%block name="tabs">
    <li><a href="#animedb-settings">${_('AnimeDB Settings')}</a></li>
    <li><a href="#anime-look-feel">${_('Look &amp; Feel')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="saveAnime" method="post">

        <!-- /component-group //-->
        <div id="animedb-settings" class="component-group">
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
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" class="enabler" name="use_anidb"
                                       id="use_anidb" ${('', 'checked="checked"')[bool(settings.USE_ANIDB)]} />
                                <label for="use_anidb">${_('should SickChill use data from AniDB?')}</label>
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
                                                   value="${settings.ANIDB_USERNAME}"
                                                   class="form-control input-sm input350 pull-left" autocapitalize="off"
                                                   autocomplete="no" title="Username"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span class="component-desc">${_('username of your AniDB account')}</span>
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
                                            <input
                                                type="password" name="anidb_password" id="anidb_password" value="${settings.ANIDB_PASSWORD|hide}"
                                                class="form-control input-sm input350 pull-left" autocomplete="no" autocapitalize="off" title="Password"
                                            />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span class="component-desc">${_('password of your AniDB account')}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('AniDB MyList')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 component-desc">
                                    <input type="checkbox" name="anidb_use_mylist"
                                           id="anidb_use_mylist" ${('', 'checked="checked"')[bool(settings.ANIDB_USE_MYLIST)]}/>
                                    <label for="anidb_use_mylist">${_('do you want to add the PostProcessed episodes to the MyList?')}</label>
                                </div>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>
        </div>

        <!-- /component-group //-->
        <div id="anime-look-feel" class="component-group">
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
                                <label class="component-title">${_('Split show lists')}</label>
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                <input type="checkbox" class="enabler" name="split_home"
                                       id="split_home" ${('', 'checked="checked"')[bool(settings.ANIME_SPLIT_HOME)]} title="Split"/>
                                <label for="split_home">${_('separate anime and normal shows in groups')}</label>
                            </div>
                        </div>
                    </fieldset>
                </div>

                <div id="content_split_home">
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-3 col-sm-4 col-xs-12">
                                    <label class="component-title">${_('Split in tabs')}</label>
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-8 col-xs-12 pull-right component-desc">
                                    <input type="checkbox" name="split_home_in_tabs"
                                           id="split_home_in_tabs" ${('', 'checked="checked"')[bool(settings.ANIME_SPLIT_HOME_IN_TABS)]} title="Split in tabs"/>
                                    <label for="split_home_in_tabs">${_('use tabs for when splitting show lists')}</label>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
        </div>

    </form>
</%block>
