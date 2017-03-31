#!/usr/bin/env bash

if [ "$TRAVIS_PULL_REQUEST" == "false" ] && [ "$TRAVIS_BRANCH" != "master" ]; then

  if [ -z "$CROWDIN_API_KEY" ]; then
    echo -e "\$CROWDIN_API_KEY is undefined or empty"
    # exit 1
  fi

  echo -e "[ 1/10] Installing babel, mako and crowdin-cli-py"
  pip install --upgrade babel mako crowdin-cli-py > /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi

  echo -e "[ 2/10] Configuring git..."
  git config --global user.name "SickRage"
  git config --global user.email sickrage2@gmail.com
  git config --global push.default simple # push only current branch

  echo -e "[ 3/10] Extracting strings..."
  python setup.py extract_messages > /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi

  echo -e "[ 4/10] Updating translations..."
  python setup.py update_catalog > /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi

  echo -e "[ 5/10] Uploading to Crowdin..."
  crowdin-cli-py upload sources #> /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi
  
  echo -e "[ 6/10] Downloading Crowdin..."
  crowdin-cli-py download #> /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi
  
  echo -e "[ 7/10] Compiling translations..."
  python setup.py compile_catalog > /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi
  
  echo -e "[ 8/10] Converting translations to json..."
  grunt po2json > /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi

  git diff-index --quiet HEAD -- locale/ # check if locale files have actually changed
  if [ $? == 0 ]; then # check return value, 0 is clean, otherwise is dirty
    echo -e "No need to update translations."
    exit 1
  fi

  echo -e "[ 9/10] Commiting translations..."
  # git remote rm origin
  # git remote add origin https://usernme:$GH_TOKEN@github.com/SickRage/SickRage.git

  # git commit -q -m "Update translations (build $TRAVIS_BUILD_NUMBER)" -- locale/
  git commit --dry-run -m "Update translations (build $TRAVIS_BUILD_NUMBER)" -- locale/

  echo -e "[10/10] Pushing translations to '$TRAVIS_BRANCH' branch"
  git push --dry-run -q -f origin $TRAVIS_BRANCH > /dev/null
  if [ $? != 0 ]; then
    echo -e "-!- An error has occurred."
    exit 1
  fi
  
  echo -e "Done!"
else
	echo -e "Nothing to do here (This is a PR or 'master' branch)"
fi
