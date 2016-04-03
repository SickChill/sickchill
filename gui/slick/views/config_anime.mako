<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>
<%block name="content">
<div id="content960">
<h1 class="header">${header}</h1>
<div id="config">
    <div id="config-content">

        <form id="configForm" action="saveAnime" method="post">

            <div id="config-components">
                <ul>
                    <li><a href="#animedb-settings">${_('AnimeDB Settings')}</a></li>
                    <li><a href="#anime-look-feel">${_('Look &amp; Feel')}</a></li>
                </ul>

                <div id="animedb-settings" class="tab-pane active component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-anime" title="AniDB"></span>
                        <h3><a href="${anon_url('http://anidb.info')}" onclick="window.open(this.href, '_blank'); return false;">AniDB</a></h3>
                        <p>${_('AniDB is non-profit database of anime information that is freely open to the public')}</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <input type="checkbox" class="enabler" name="use_anidb" id="use_anidb" ${('', 'checked="checked"')[bool(sickbeard.USE_ANIDB)]} />
                            <label for="use_notifo">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">${_('Should SickRage use data from AniDB?')}</span>
                            </label>
                        </div>

                        <div id="content_use_anidb">
                            <div class="field-pair">
                                <label class="nocheck">
                                    <span class="component-title">${_('AniDB Username')}</span>
                                    <input type="text" name="anidb_username" id="anidb_username" value="${sickbeard.ANIDB_USERNAME}" class="form-control input-sm input350" autocapitalize="off" autocomplete="no" />
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Username of your AniDB account')}</span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label class="nocheck">
                                    <span class="component-title">${_('AniDB Password')}</span>
                                    <input type="password" name="anidb_password" id="anidb_password" value="${sickbeard.ANIDB_PASSWORD}" class="form-control input-sm input350" autocomplete="no" autocapitalize="off" />
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Password of your AniDB account')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <input type="checkbox" name="anidb_use_mylist" id="anidb_use_mylist" ${('', 'checked="checked"')[bool(sickbeard.ANIDB_USE_MYLIST)]}/>
                                <label>
                                    <span class="component-title">${_('AniDB MyList')}</span>
                                    <span class="component-desc">${_('Do you want to add the PostProcessed Episodes to the MyList ?')}</span>
                                </label>
                            </div>
                        </div>
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                    </fieldset>

                </div><!-- /component-group //-->

                <div id="anime-look-feel" class="tab-pane component-group">

                    <div class="component-group-desc">
                        <span class="icon-notifiers-look" title="look"></span>
                        <h3>${_('Look and Feel')}</h3>
                        <p>${_('How should the anime functions show and behave.')}</p>
                   </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <input type="checkbox" class="enabler" name="split_home" id="split_home" ${('', 'checked="checked"')[bool(sickbeard.ANIME_SPLIT_HOME)]}/>
                            <label for="use_notifo">
                                <span class="component-title">${_('Split show lists')}</span>
                                <span class="component-desc">${_('Separate anime and normal shows in groups')}</span>
                            </label>
                        </div>
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                   </fieldset>
                </div><!-- /component-group //-->

                <br><input type="submit" class="btn config_submitter" value="${_('Save Changes')}" /><br>

            </div><!-- /config-components //-->

        </form>
    </div>
</div>
</%block>
