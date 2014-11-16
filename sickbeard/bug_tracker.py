import sickbeard

class BugTracker:
    def submit_bug(self, title, error):
        return sickbeard.gh.create_issue(title, error, labels=[sickbeard.gh().get_label(sickbeard.BRANCH)])