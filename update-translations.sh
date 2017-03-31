#!/usr/bin/env bash
# if [ "$TRAVIS_PULL_REQUEST" == "false" ] && [ "$TRAVIS_BRANCH" == "develop" ]; then
# if [ "$TRAVIS_BRANCH" == "develop" ]; then
  # if [ -z "$CROWDIN_API_KEY" ]; then
    # echo -e "CROWDIN_API_KEY is not defined or empty"
    # exit 1
  # fi
  
  echo -e "Setting up..."
  pip install --upgrade babel
  pip install --upgrade crowdin-cli-py
  pip install --upgrade mako
  
  git config --global user.name "SickRage"
  git config --global user.email sickrage2@gmail.com
  git config --global push.default simple # push only current branch

  echo -e "Updating translations..."
  python setup.py extract_messages
  python setup.py update_catalog
  crowdin-cli-py upload sources
  crowdin-cli-py download
  python setup.py compile_catalog
  grunt po2json

  git diff-index --quiet HEAD -- locale/ # check if locale files have actually changed
  if [ $? == 0 ]; then # check return value, 0 is clean, otherwise is dirty
	echo -e "No need to update translations."
	exit 1
  fi

  echo -e "Commiting and pushing translations..."
  echo -e "commit msg: Update translations (build $TRAVIS_BUILD_NUMBER)" # remove later
  # git remote rm origin
  # git remote add origin https://usernme:$GH_TOKEN@github.com/SickRage/SickRage.git

  # git add -f -- locale/
  # git commit -q -m "Update translations (build $TRAVIS_BUILD_NUMBER)"
  git commit --dry-run -m "Update translations (build $TRAVIS_BUILD_NUMBER)"
  # git push -f origin develop > /dev/null
  
  echo -e "Done!"
# fi
