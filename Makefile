test-all:
	@ nosetests --cover-package=sickrage --verbosity=1 --cover-erase

test-all-with-coverage:
	@ nosetests --cover-package=sickrage --verbosity=1 --cover-erase --with-coverage