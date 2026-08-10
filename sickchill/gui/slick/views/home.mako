<%inherit file="/layouts/main.mako" />
<%!
    from sickchill import settings
%>
<%block name="metas">
    <meta data-var="max_download_count" data-content="${max_download_count}" />
</%block>

<%block name="content">

    <%include file="/inc_home_menu.mako" />

    % if settings.ANIME_SPLIT_HOME:
        % if settings.ANIME_SPLIT_HOME_IN_TABS:
        <!-- Split in tabs -->
        <div id="showTabs">
            <!-- Nav tabs -->
            <ul>
                % for cur_show_list in sorted_show_lists:
                    % if cur_show_list[1]:
                        <li><a href="#${cur_show_list[0].lower()}TabContent" id="${cur_show_list[0].lower()}Tab">${cur_show_list[0]}</a></li>
                    % endif
                % endfor
            </ul>
            <!-- Tab panes -->
        <div>
        % endif
        % for cur_show_list in sorted_show_lists:
            % if cur_show_list[1]:
            <% curListType = cur_show_list[0] %>
                <div id=${("showsTabContent", "animeTabContent")[curListType == "Anime"]}>
                    <div class="row home-container">
                        <div class="col-md-12">
                            % if not settings.ANIME_SPLIT_HOME_IN_TABS:
                                <h1 class="header">${(_('Shows'), _('Anime'))[curListType == "Anime"]}</h1>
                            % endif
                            % if settings.HOME_LAYOUT == 'poster':
                                <div class="loading-spinner"></div>
                            % endif
                            <div class="row">
                                <div class="col-md-12">
                                        <%include file="/inc_home_show_list.mako" args="curListType=curListType, myShowList=cur_show_list[1]" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            % endif
        % endfor
        % if settings.ANIME_SPLIT_HOME_IN_TABS:
            </div>
            </div>
        % endif
    % else:
        <!-- no split -->
        <div class="row home-container">
            <div class="col-md-12">
                % if settings.HOME_LAYOUT == 'poster':
                    <div class="loading-spinner"></div>
                % endif
                % for cur_show_list in sorted_show_lists:
                    % if cur_show_list[1]:
                        <div class="row">
                            <div class="col-md-12">
                                <%include file="/inc_home_show_list.mako" args="curListType=cur_show_list[0], myShowList=cur_show_list[1]" />
                            </div>
                        </div>
                    % endif
                % endfor
            </div>
        </div>
    % endif

</%block>
