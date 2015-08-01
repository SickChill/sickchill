<%
    import sickbeard
    import datetime
    from sickbeard.common import *
    from sickbeard import db

    global title="Home"
    global header="Restarting SickRage"


    global topmenu="home"
    import os.path
    include $os.path.join($sickbeard.PROG_DIR, "gui/slick/interfaces/default/inc_top.tmpl")

    include $os.path.join($sickbeard.PROG_DIR, "gui/slick/interfaces/default/restart_bare.tmpl")

    include $os.path.join($sickbeard.PROG_DIR,"gui/slick/interfaces/default/inc_bottom.tmpl")
%>
