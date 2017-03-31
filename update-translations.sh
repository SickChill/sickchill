#!/usr/bin/env bash

if [ "$TRAVIS_BRANCH" == "develop" ]; then # either the pushed branch or the pull request base branch
  if [ -z "$CROWDIN_API_KEY" ]; then
    echo -e "\$CROWDIN_API_KEY is undefined or empty"
    # exit 1
  fi
  
  echo -e "[1/9] Installing babel, mako and crowdin-cli-py"
  pip install --upgrade babel mako crowdin-cli-py
  
  echo -e "[2/9] Configuring git..."
  git config --global user.name "SickRage"
  git config --global user.email sickrage2@gmail.com
  git config --global push.default simple # push only current branch

  echo -e "[3/9] Extracting strings..."
  python setup.py extract_messages > /dev/null
  
  echo -e "[4/9] Updating translations..."
  python setup.py update_catalog > /dev/null
  
  echo -e "[5/9] Uploading to Crowdin..."
  crowdin-cli-py upload sources #> /dev/null
  
  echo -e "[6/9] Downloading Crowdin..."
  crowdin-cli-py download #> /dev/null
  
  echo -e "[7/9] Compiling translations..."
  python setup.py compile_catalog > /dev/null
  
  echo -e "[8/9] Converting translations to json..."
  grunt po2json > /dev/null

  git diff-index --quiet HEAD -- locale/ # check if locale files have actually changed
  if [ $? == 0 ]; then # check return value, 0 is clean, otherwise is dirty
	echo -e "No need to update translations."
	exit 1
  fi

  echo -e "[9/9] Commiting and pushing translations..."
  # git remote rm origin
  # git remote add origin https://usernme:$GH_TOKEN@github.com/SickRage/SickRage.git

  # git commit -q -m "Update translations (build $TRAVIS_BUILD_NUMBER)" -- locale/
  git commit --dry-run -m "Update translations (build $TRAVIS_BUILD_NUMBER)" -- locale/
  if [ "$TRAVIS_PULL_REQUEST" == "true" ] && [ "$TRAVIS_PULL_REQUEST_SLUG" == "SickRage/SickRage" ]; then
    git push --dry-run -f origin $TRAVIS_PULL_REQUEST_BRANCH > /dev/null
  else
    git push --dry-run -f origin develop > /dev/null
  fi
  
  echo -e "[-/-] Done!"
fi
