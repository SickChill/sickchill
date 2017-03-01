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
         %if sickbeard.ANIME_SPLIT_HOME_IN_TABS:
             <!-- Split in tabs -->
             <div id="showTabs">
                 <!-- Nav tabs -->
                 <ul>
                     <li>
                         <a href="#showsTabContent" id="showsTab">Shows</a>
                     </li>
                     <li>
                         <a href="#animeTabContent" id="animeTab">Anime</a>
                     </li>
                 </ul>
                 <!-- Tab panes -->
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
                 </div>
             </div>
         %else:
             <!-- Simple split in tables -->
             <div class="row home-container">
                 <div class="col-md-12">
                     <h1 class="header">${_('Shows')}</h1>
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
             <div class="row home-container">
                 <div class="col-md-12">
                     <br>
                     <h1 class="header">${_('Anime')}</h1>
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
         %endif
    %else:
        <!-- no split -->
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
