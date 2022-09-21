#!/bin/bash --
# Author: @DirtyCajunRice

LOCATION=/opt/sickchill

# Check if ran by root
if [[ $UID -ne 0 ]]; then
  echo 'Script must be run as root'
  exit 1
fi

# Check for distro; continue if debian/ubuntu || exit
if [[ $(cat /etc/issue) =~ Debian ]]; then
  distro=debian
elif [[ $(cat /etc/issue) =~ Ubuntu ]]; then
  distro=ubuntu
else
  echo "This script will only work on Debian and Ubuntu Distros, but you are using $(cat /etc/issue)"
  exit 1
fi

# Get external ip address (checking 3 sites for redundancy)
for i in 'ipecho.net/plain' 'ifconfig.me' 'checkip.amazonaws.com'; do
  external_ip=$(curl -s ${i})
  [[ ! ${external_ip} ]] || break
done

# Get internal ip address
internal_ip=$(ip r g 8.8.8.8 | awk 'NR==1{print $7};')

# Installed whiptail for script prerequisite
apt-get -qq install whiptail -y

function check_packages {
  packages=$(dpkg -l unrar openssl libssl-dev python3.9 2>&1 | grep "no packages" | awk '{ print $6 }' | tr '\n' ' ')
}

# Check to see what SickChill Dependencies are missing
check_packages
if [[ ${packages} ]]; then
  # Show Whiptail and install required files
  {
    i=1
    # shellcheck disable=SC2086
    while read -r; do
      i=$(( i + 1 ))
      echo ${i}
    done < <(apt-get update && apt install ${packages} -y)
  } | whiptail --title "Progress" --gauge "Installing $packages" 8 80 0
fi

# Check to see if all prior packages were installed successfully. if not exit 1 and display whiptail issues
check_packages
if [[ ${packages} ]]; then
  whiptail --title "Package Installation Failed" --msgbox \
"These Packages have failed:
${packages}
Please resolve these issues and restart the install script" 15 66
  exit 1
fi

# Check to see if sickchill exists; If not make user/group
if [[ ! "$(getent group sickchill)" ]]; then
  echo "Adding SickChill Group"
  addgroup --system sickchill
  if [[ $? != 0 ]]; then
    whiptail --title "Failed to create sickchill user" --msgbox "Failed to create sickchill user" 8 128
    exit 1
  fi
fi

if [[ ! "$(getent passwd sickchill)" ]]; then
  echo "Adding SickChill User"
  adduser --disabled-password --system --home /var/lib/sickchill --gecos "SickChill" --ingroup sickchill sickchill
  if [[ $? != 0 ]]; then
    whiptail --title "Failed to disable password for sickchill user" --msgbox "Failed to disable password for sickchill user" 8 128
    exit 1
  fi
fi

if [[ ${SUDO_USER} != "root" ]]; then
  username=$(whiptail --title 'Add user to group group?' --inputbox "Do you want to add a user to the sickchill group?" --ok-button "Add" --cancel-button "Skip" 8 128 3>&1 1>&2 2>&3)
  if [[ ${#username} -gt 0 ]]; then
    echo "Adding ${username} to the sickchill group"
    sudo usermod -a -G sickchill ${username}
    if [[ $? != 0 ]]; then
      whiptail --title "Failed to add user to group" --msgbox "Failed to add ${username} to the sickchill group" 8 128
      exit 1
    fi
  fi
fi

if [[ -d ${LOCATION} ]]; then
  whiptail --title 'Rename?' --yesno "${LOCATION} already exists, do you want to rename it? If not, we will exit and you can fix the issues and re-run this script" 8 140
  if [[ $? == 0 ]]; then
    echo "Renaming old SickChill Folder to ${LOCATION}.old"
    mv ${LOCATION} ${LOCATION}.old
    if [[ $? != 0 ]]; then
      whiptail --title "Failed to rename ${LOCATION}" --msgbox "Failed to rename ${LOCATION} to ${LOCATION}.old" 8 128
      exit 1
    fi
  else
    echo "Please fix the issues and re-run this script"
    exit 1
  fi
fi

if [[ ! -d ${LOCATION} ]]; then
  echo "Creating SickChill Folder"
  mkdir -p ${LOCATION}
  if [[ $? != 0 ]]; then
    whiptail --title "Failed to create ${LOCATION}" --msgbox "Failed to create ${LOCATION}" 8 128
    exit 1
  fi
  chown -R sickchill:sickchill ${LOCATION}
  if [[ $? != 0 ]]; then
    whiptail --title "Failed to change ownership of ${LOCATION}" --msgbox "Failed to change ownership of ${LOCATION}" 8 128
    exit 1
  fi
fi

echo "Creating virtual environment"
sudo -u sickchill -g sickchill python3 -m venv ${LOCATION}
if [[ $? != 0 ]]; then
  whiptail --title "Failed to create virtual environment" --msgbox "Failed to create virtual environment" 8 128
  exit 1
fi

OS_NAME=$(cat /etc/os-release | grep -oP "(?:^ID=)(.*)" | sed 's|ID=||')
echo "Checking if we should add an index for your platform OS: ${OS_NAME}"
case "$OS_NAME" in
    ubuntu)
            EXTRA_INDEX=" --find-links=https://wheel-index.linuxserver.io/ubuntu/";;
    alpine)
            EXTRA_INDEX=" --find-links=https://wheel-index.linuxserver.io/alpine/ --extra-index-url=https://alpine-wheels.github.io/index";;
    raspbian|osmc)
            EXTRA_INDEX=" --extra-index-url=https://www.piwheels.org/simple";;
        *)
            echo "No extra indexes needed that we know of";;
esac


echo "Installing SickChill"
sudo -u sickchill -g sickchill ${LOCATION}/bin/pip install -U pip setuptools wheel ${EXTRA_INDEX}
if [[ $? != 0 ]]; then
  whiptail --title "Failed to update pip" --msgbox "Failed to update pip" 8 128
  exit 1
fi

sudo -u sickchill -g sickchill ${LOCATION}/bin/pip install -U sickchill ${EXTRA_INDEX}
if [[ $? != 0 ]]; then
  whiptail --title "Failed to install SickChill" --msgbox "Failed to install SickChill" 8 128
  exit 1
fi

function download_service_file() {
  curl https://raw.githubusercontent.com/SickChill/SickChill/master/contrib/runscripts/${1} > ${2}
  export SERVICE_FILE=${2}
  if [[ $? != 0 ]]; then
    whiptail --title "Failed to download ${1}" --msgbox "Failed to download ${1}" 8 128
    exit 1
  fi

  chown root:root ${2} && chmod ${3} ${2}
  if [[ $? != 0 ]]; then
    whiptail --title "Failed to set permissions on ${2}" --msgbox "Failed to set permissions on ${2}" 8 128
    exit 1
  fi
}
# Depending on Distro, cp the service script, then change the owner/group and change the permissions. Finally
# start the service
if [[ $(/sbin/init --version 2>/dev/null) =~ upstart ]]; then
  echo "Copying Startup Script To Upstart"
  download_service_file "init.upstart" "/etc/init/sickchill.conf" "644"
  echo "Starting SickChill"
  service sickchill start
elif [[ $(systemctl) =~ -\.mount ]]; then
  echo "Copying Startup Script To systemd"
  download_service_file "init.systemd" "/etc/systemd/system/sickchill.service" "644"
  echo "Starting SickChill"
  systemctl -q enable sickchill && systemctl -q start sickchill
else
  echo "Copying Startup Script To init"
  download_service_file "init.${distro}" "/etc/init.d/sickchill" "755"
  echo "Starting SickChill"
  update-rc.d sickchill defaults && service sickchill start
fi

SERVICE_RESULE=$?

echo "If you run sickchill as the sickchill user like this:"
echo ">> sudo -u sickchill -g sickchill PATH= /opt/sickchill/bin/SickChill"
echo "Your config.ini and database will be in '/var/lib/sickchill/.config/sickchill/"
echo "If you run sickchill as the sickchill user like this:"
echo ">> PATH= /opt/sickchill/bin/SickChill"
echo "Your config.ini and database will be in '/home/${SUDO_USER}/.config/sickchill/"
echo "If you run sickchill as the sickchill user like this:"
echo ">> PATH= /opt/sickchill/bin/SickChill --datadir=/opt/sickchill"
echo "Your config.ini and database will be in '/opt/sickchill'"
echo "It is recommended to run sickchill as the sickchill user, as in the first example"
echo "To update sickchill, run the following command:"
echo ">> sudo -u sickchill -g sickchill ${LOCATION}/bin/pip install -U sickchill"

if [[ $SERVICE_RESULT != 0 ]]; then
  whiptail --title "Failed to start SickChill" --msgbox "Failed to start SickChill, edit your service file at ${SERVICE_FILE}" 8 128
  echo "Failed to start SickChill, edit your service file at ${SERVICE_FILE}"
  exit 1
fi

# Finish by explaining the script is finished and give them the relevant IP addresses
whiptail --title Complete --msgbox \
"Check that everything has been set up correctly by going to:

          Internal IP: http://$internal_ip:8081
                             OR
          External IP: http://$external_ip:8081

 make sure to add sickchill to your download clients group
 and check the log above for information about running sickchill" 15 66
