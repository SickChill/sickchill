<%!
    import sickbeard
    import datetime
    from sickbeard import db
    from sickbeard.common import Quality, SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST
    import re
%>
<%
    sbRoot = sickbeard.WEB_ROOT
%>
    </div> <!-- /content -->
</div> <!-- /contentWrapper -->

<footer>
<div class="footer clearfix">
<%
    myDB = db.DBConnection()
    today = str(datetime.date.today().toordinal())
    status_quality = '(%s)' % ','.join([str(quality) for quality in Quality.SNATCHED + Quality.SNATCHED_PROPER])
    status_download = '(%s)' % ','.join([str(quality) for quality in Quality.DOWNLOADED + [ARCHIVED]])

    sql_statement = 'SELECT ' \
    + '(SELECT COUNT(*) FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1 AND status IN %s) AS ep_snatched, ' % status_quality \
    + '(SELECT COUNT(*) FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1 AND status IN %s) AS ep_downloaded, ' % status_download \
    + '(SELECT COUNT(*) FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1 AND ((airdate <= %s AND (status = %s OR status = %s)) ' % (today, str(SKIPPED), str(WANTED)) \
    + ' OR (status IN %s) OR (status IN %s))) AS ep_total FROM tv_episodes tv_eps LIMIT 1' % (status_quality, status_download)

    sql_result = myDB.select(sql_statement)

    shows_total = len(sickbeard.showList)
    shows_active = len([show for show in sickbeard.showList if show.paused == 0 and show.status == "Continuing"])

    if sql_result:
        ep_snatched = sql_result[0]['ep_snatched']
        ep_downloaded = sql_result[0]['ep_downloaded']
        ep_total = sql_result[0]['ep_total']
    else:
        ep_snatched = 0
        ep_downloaded = 0
        ep_total = 0

    ep_percentage = '' if ep_total == 0 else '(<span class="footerhighlight">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))

    try:
        localRoot = sbRoot
    except NotFound:
        localRoot = ''

    try:
        localheader = header
    except NotFound:
        localheader = ''
%>

        <span class="footerhighlight">${shows_total}</span> Shows (<span class="footerhighlight">${shows_active}</span> Active)
        | <span class="footerhighlight">${ep_downloaded}</span>

        % if ep_snatched:
        <span class="footerhighlight"><a href="${localRoot}/manage/episodeStatuses?whichStatus=2" title="View overview of snatched episodes">+${ep_snatched}</a></span> Snatched
        % endif

                &nbsp;/&nbsp;<span class="footerhighlight">${ep_total}</span> Episodes Downloaded ${ep_percentage}
        | Daily Search: <span class="footerhighlight">${str(sickbeard.dailySearchScheduler.timeLeft()).split('.')[0]}</span>
        | Backlog Search: <span class="footerhighlight">${str(sickbeard.backlogSearchScheduler.timeLeft()).split('.')[0]}</span>
    </div>
        <!--
        <ul style="display: table; margin: 0 auto; font-size: 12px; list-style-type: none; padding: 0; padding-top: 10px;">
            <li><a href="${sbRoot}/manage/manageSearches/forceVersionCheck"><img src="${sbRoot}/images/menu/update16.png" alt="" width="16" height="16" style="vertical-align:middle;" />Force Version Check</a></li>
            <li><a href="${sbRoot}/home/restart/?pid=${sbPID}" class="confirm"><img src="${sbRoot}/images/menu/restart16.png" alt="" width="16" height="16" style="vertical-align:middle;" />Restart</a></li>
            <li><a href="${sbRoot}/home/shutdown/?pid=${sbPID}" class="confirm"><img src="${sbRoot}/images/menu/shutdown16.png" alt="" width="16" height="16" style="vertical-align:middle;" />Shutdown</a></li>
        </ul>
        -->
</footer>

</body>
</html>
