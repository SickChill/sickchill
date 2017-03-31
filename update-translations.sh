#!/usr/bin/env bash
# if [ "$TRAVIS_PULL_REQUEST" == "false" ] && [ "$TRAVIS_BRANCH" == "develop" ]; then
#if [ "$TRAVIS_BRANCH" == "develop" ]; then
  if [ ! -z "$CROWDIN_API_KEY" ]; then
    echo -e "CROWDIN_API_KEY is not defined or empty"
  exit 1
  fi
  
  echo -e "Setting up..."
  pip install --upgrade babel
  pip install --upgrade crowdin-cli-py
  
  git config --global user.name "SickRage"
  git config --global user.email sickrage2@gmail.com
  git config --global push.default simple # push only current branch

  echo -e "Updating translations..."
  setup.py extract_messages
  setup.py update_catalog
  crowdin-cli-py upload sources
  crowdin-cli-py download
  setup.py compile_catalog
  grunt po2json

  echo -e "Commiting and pushing translations..."
  #git remote rm origin
  #git remote add origin https://usernme:$GH_TOKEN@github.com/SickRage/SickRage.git

  git add -f -- locale/
  git commit -m "Update translations (build $TRAVIS_BUILD_NUMBER)"
  #git push -f origin develop > /dev/null
#fi
