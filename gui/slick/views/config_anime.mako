<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>

<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/configAnime.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/config.js?${sbPID}"></script>
</%block>
<%block name="content">
<div id="content960">
<h1 class="header">${header}</h1>
<div id="config">
    <div id="config-content">

        <form id="configForm" action="saveAnime" method="post">

            <div id="config-components">

                <ul>
                    <li><a href="#core-component-group1">AnimeDB Settings</a></li>
                    <li><a href="#core-component-group2">Look &amp; Feel</a></li>
                </ul>

                <div id="core-component-group1" class="tab-pane active component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${sbRoot}/images/anidb24.png" alt="AniDB" title="AniDB" width="24" height="24" />
                        <h3><a href="${anon_url('http://anidb.info')}" onclick="window.open(this.href, '_blank'); return false;">AniDB</a></h3>
                        <p>AniDB is non-profit database of anime information that is freely open to the public</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <input type="checkbox" class="enabler" name="use_anidb" id="use_anidb" ${('', 'checked="checked"')[bool(sickbeard.USE_ANIDB)]} />
                            <label for="use_notifo">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">Should Sick Beard use data from AniDB?</span>
                            </label>
                        </div>

                        <div id="content_use_anidb">
                            <div class="field-pair">
                                <label class="nocheck">
                                    <span class="component-title">AniDB Username</span>
                                    <input type="text" name="anidb_username" id="anidb_username" value="${sickbeard.ANIDB_USERNAME}" class="form-control input-sm input350" />
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Username of your AniDB account</span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label class="nocheck">
                                    <span class="component-title">AniDB Password</span>
                                    <input type="password" name="anidb_password" id="anidb_password" value="${sickbeard.ANIDB_PASSWORD}" class="form-control input-sm input350" />
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Password of your AniDB account</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <input type="checkbox" name="anidb_use_mylist" id="anidb_use_mylist" ${('', 'checked="checked"')[bool(sickbeard.ANIDB_USE_MYLIST)]}/>
                                <label>
                                    <span class="component-title">AniDB MyList</span>
                                    <span class="component-desc">Do you want to add the PostProcessed Episodes to the MyList ?</span>
                                </label>
                            </div>
                        </div>
                        <input type="submit" class="btn config_submitter" value="Save Changes" />
                    </fieldset>

                </div><!-- /component-group //-->

                <div id="core-component-group2" class="tab-pane component-group">

                    <div class="component-group-desc">
                        <h3>Look and Feel</h3>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <input type="checkbox" class="enabler" name="split_home" id="split_home" ${('', 'checked="checked"')[bool(sickbeard.ANIME_SPLIT_HOME)]}/>
                            <label for="use_notifo">
                                <span class="component-title">Split show lists</span>
                                <span class="component-desc">Separate anime and normal shows in groups</span>
                            </label>
                        </div>
                        <input type="submit" class="btn config_submitter" value="Save Changes" />
                   </fieldset>
                </div><!-- /component-group //-->

                <br/><input type="submit" class="btn config_submitter" value="Save Changes" /><br/>

            </div><!-- /config-components //-->

        </form>
    </div>
</div>
</%block>
