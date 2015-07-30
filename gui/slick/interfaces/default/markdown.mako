<%!
    import sickbeard
    from sickbeard.common import *

    import os.path
    include file=os.path.join(sickbeard.PROG_DIR, "gui/slick/interfaces/default/inc_top.mako")
%>
${data}

% include os.path.join(sickbeard.PROG_DIR, "gui/slick/interfaces/default/inc_bottom.mako")
