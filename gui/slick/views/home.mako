<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="metas">
    <meta data-var="max_download_count" data-content="${max_download_count}"/>
</%block>

<%block name="content">

    <%include file="/inc_home_menu.mako"/>

    % if sickbeard.ANIME_SPLIT_HOME:
    <!-- Nav tabs -->
    <div id="showTabs">
        <ul>
            <li>
                <a href="#showsTabContent" id="showTab">Shows</a>
            </li>
            % if sickbeard.ANIME_SPLIT_HOME:
                <li>
                    <a href="#animeTabContent" id="animeTab">Anime</a>
                </li>
            % endif
        </ul>
        <!-- Tab panes -->
        <div id="showTabs">
            <div>
                <div id="showsTabContent">
                    <div class="row home-container">
                        <div class="col-md-12">
                            % if sickbeard.HOME_LAYOUT == 'poster':
                                <div class="loading-spinner"></div>
                            % endif
                            % for curShowlist in showlists:
                                <div class="row">
                                    <div class="col-md-12">
                                        <% curListType = curShowlist[0] %>
                                        <% myShowList = list(curShowlist[1]) %>
                                        % if curListType != "Anime":
                                            <%include file="/inc_home_showList.mako" args="curListType=curListType, myShowList=myShowList"/>
                                        % endif
                                    </div>
                                </div>
                            % endfor
                        </div>
                    </div>
                </div>
                % if sickbeard.ANIME_SPLIT_HOME:
                    <div id="animeTabContent">
                        <div class="row home-container">
                            <div class="col-md-12">
                                % if sickbeard.HOME_LAYOUT == 'poster':
                                    <div class="loading-spinner"></div>
                                % endif
                                % for curShowlist in showlists:
                                    <div class="row">
                                        <div class="col-md-12">
                                            <% curListType = curShowlist[0] %>
                                            <% myShowList = list(curShowlist[1]) %>
                                            % if curListType == "Anime":
                                                <%include file="/inc_home_showList.mako" args="curListType=curListType, myShowList=myShowList"/>
                                            % endif
                                        </div>
                                    </div>
                                % endfor
                            </div>
                        </div>
                    </div>
                %endif
            </div>
        </div>
    </div>
    %else:
        <div class="row home-container">
            <div class="col-md-12">
                % if sickbeard.HOME_LAYOUT == 'poster':
                    <div class="loading-spinner"></div>
                % endif
                % for curShowlist in showlists:
                    <div class="row">
                        <div class="col-md-12">
                            <% curListType = curShowlist[0] %>
                            <% myShowList = list(curShowlist[1]) %>
                            <%include file="/inc_home_showList.mako" args="curListType=curListType, myShowList=myShowList"/>
                        </div>
                    </div>
                % endfor
            </div>
        </div>
    %endif

</%block>
