#!/bin/bash --
# Original Author: @DirtyCajunRice
# Updated for Debian 13 (Trixie) and Ubuntu 24.04 (Noble)

LOCATION=/opt/sickchill

# Check if ran by root
if [[ $UID -ne 0 ]]; then
  echo 'Script must be run as root'
  exit 1
fi

# Check for distro using /etc/os-release
if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  case "${ID}" in
    ubuntu|debian)
      distro="${ID}"
      ;;
    *)
      echo "This script will only work on Debian and Ubuntu Distros, but you are using ${ID}"
      exit 1
      ;;
  esac
else
  echo "Cannot detect distribution (/etc/os-release missing)"
  exit 1
fi

echo "Detected distro: ${distro} (${VERSION_ID:-unknown})"

# Get external ip address (checking 3 sites for redundancy)
for i in 'ipecho.net/plain' 'ifconfig.me' 'checkip.amazonaws.com'; do
  external_ip=$(curl -s "${i}")
  [[ ! ${external_ip} ]] || break
done

# Get internal ip address
internal_ip=$(ip r g 8.8.8.8 | awk 'NR==1{print $7};')

# Update package lists
apt-get update -qq || { echo "apt-get update failed"; exit 1; }

# Install whiptail for script prerequisite
apt-get install -y whiptail || { echo "Failed to install whiptail"; exit 1; }

# Required packages for SickChill on Debian 13 / Ubuntu 24.04
# - python3-venv is required for `python3 -m venv`
# - build tools + headers are needed to compile native wheels (greenlet, cryptography, lxml, etc.)
# - mediainfo for pymediainfo; unrar (rarfile) is optional — Debian packages it in non-free
REQUIRED_PACKAGES=(
  python3
  python3-venv
  python3-pip
  python3-dev
  build-essential
  libffi-dev
  libssl-dev
  libxml2-dev
  libxslt1-dev
  git
  curl
  mediainfo
)

echo "Installing required packages: ${REQUIRED_PACKAGES[*]}"
if ! apt-get install -y "${REQUIRED_PACKAGES[@]}"; then
  whiptail --title "Package Installation Failed" --msgbox \
"Failed to install one or more required packages.
Please resolve package issues and re-run this script." 12 70
  exit 1
fi

# unrar is in Debian non-free; do not fail the install if APT cannot fetch it
if ! command -v unrar >/dev/null 2>&1; then
  echo "Installing optional package: unrar"
  if ! apt-get install -y unrar; then
    echo "unrar was not installed (needed for rarfile). On Debian enable non-free, then:"
    echo "  sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources"
    echo "  apt-get update && apt-get install -y unrar"
  fi
fi

# Check to see if sickchill exists; If not make user/group
if [[ ! "$(getent group sickchill)" ]]; then
  echo "Adding SickChill Group"
  if ! addgroup --system sickchill; then
    whiptail --title "Failed to create sickchill group" --msgbox "Failed to create sickchill group" 8 128
    exit 1
  fi
fi

if [[ ! "$(getent passwd sickchill)" ]]; then
  echo "Adding SickChill User"
  if ! adduser --disabled-password --system --home /var/lib/sickchill --gecos "SickChill" --ingroup sickchill sickchill; then
    whiptail --title "Failed to create sickchill user" --msgbox "Failed to create sickchill user" 8 128
    exit 1
  fi
fi

if [[ ${SUDO_USER:-root} != "root" ]]; then
  username=${SUDO_USER}
else
  username=
fi

username=$(whiptail --title 'Add user to group?' --inputbox "Do you want to add a user to the sickchill group?" --ok-button "Add" --cancel-button "Skip" 8 128 "${username}" 3>&1 1>&2 2>&3)
if [[ ${#username} -gt 0 ]]; then
  echo "Adding $username to the sickchill group"
  if ! usermod -a -G sickchill "$username"; then
    whiptail --title "Failed to add user to group" --msgbox "Failed to add $username to the sickchill group" 8 128
    exit 1
  fi
fi

# Prompt for install source before any rename of an existing installation
if ! INSTALL_SOURCE=$(whiptail --title "SickChill Install Source" --menu \
  "Choose which version to install:" 15 60 3 \
  "release" "Latest release from PyPI (recommended)" \
  "develop" "Latest develop branch from GitHub" \
  "master"  "Latest master branch from GitHub" \
  3>&1 1>&2 2>&3); then
  echo "Install cancelled"
  exit 1
fi

case "${INSTALL_SOURCE}" in
  develop)
    SICKCHILL_SPEC="git+https://github.com/SickChill/SickChill.git@develop"
    ;;
  master)
    SICKCHILL_SPEC="git+https://github.com/SickChill/SickChill.git@master"
    ;;
  *)
    SICKCHILL_SPEC="sickchill"
    ;;
esac

python_is_311_plus() {
  "$1" -I -c "import sys; raise SystemExit(sys.version_info < (3, 11))"
}

python_has_ensurepip() {
  "$1" -I -c "import ensurepip"
}

python_has_dev_headers() {
  "$1" -I -c "import pathlib, sysconfig; raise SystemExit(not pathlib.Path(sysconfig.get_path('include')).joinpath('Python.h').is_file())"
}

PYTHON_BIN=""
for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
  candidate_path="$(command -v "${candidate}" 2>/dev/null)" || continue
  case "${candidate_path}" in
    "${LOCATION}"|"${LOCATION}"/*) continue ;;
  esac
  if ! python_is_311_plus "${candidate_path}"; then
    continue
  fi
  if ! python_has_ensurepip "${candidate_path}" || ! python_has_dev_headers "${candidate_path}"; then
    py_mm="$("${candidate_path}" -I -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
    echo "Installing python${py_mm}-dev python${py_mm}-venv for ${candidate_path}"
    apt-get install -y "python${py_mm}-dev" "python${py_mm}-venv" || true
    if ! python_has_ensurepip "${candidate_path}" || ! python_has_dev_headers "${candidate_path}"; then
      continue
    fi
  fi
  PYTHON_BIN="${candidate_path}"
  break
done
if [[ -z ${PYTHON_BIN} ]]; then
  echo "No Python 3.11+ interpreter found"
  exit 1
fi

if [[ -d ${LOCATION} ]]; then
  if whiptail --title 'Rename?' --yesno "${LOCATION} already exists, do you want to rename it? If not, we will exit and you can fix the issues and re-run this script" 8 140;
  then
    echo "Renaming old SickChill Folder to ${LOCATION}.old"
    if ! mv "${LOCATION}" "${LOCATION}.old"; then
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
  if ! mkdir -p "${LOCATION}"; then
    whiptail --title "Failed to create ${LOCATION}" --msgbox "Failed to create ${LOCATION}" 8 128
    exit 1
  fi
  if ! chown -R sickchill:sickchill "${LOCATION}"; then
    whiptail --title "Failed to change ownership of ${LOCATION}" --msgbox "Failed to change ownership of ${LOCATION}" 8 128
    exit 1
  fi
fi

echo "Creating virtual environment with $(${PYTHON_BIN} --version)"
if ! sudo -u sickchill -g sickchill "${PYTHON_BIN}" -m venv "${LOCATION}"; then
  whiptail --title "Failed to create virtual environment" --msgbox "Failed to create virtual environment. Ensure python3-venv is installed." 8 128
  exit 1
fi

OS_NAME=$(grep -oP "(?:^ID=)(.*)" < /etc/os-release | sed 's|ID=||')
echo "Checking if we should add an index for your platform OS: ${OS_NAME}"
INDEXES=()

case "$OS_NAME" in
    ubuntu)
            INDEXES+=("--find-links=https://wheel-index.linuxserver.io/ubuntu/");;
    alpine)
            INDEXES+=("--find-links=https://wheel-index.linuxserver.io/alpine/")
            INDEXES+=("--extra-index-url=https://alpine-wheels.github.io/index");;
    raspbian|osmc)
            INDEXES+=("--extra-index-url=https://www.piwheels.org/simple");;
        *)
            echo "No extra indexes needed that we know of";;
esac

WHEELS=("pip" "setuptools" "wheel")
echo "Installing" "${WHEELS[@]}"
if ! sudo -u sickchill -g sickchill "${LOCATION}/bin/pip" install -U "${WHEELS[@]}" "${INDEXES[@]}"; then
  whiptail --title "Failed to update pip" --msgbox "Failed to update pip" 8 128
  exit 1
fi

echo "Installing SickChill from: ${SICKCHILL_SPEC}"
if ! sudo -u sickchill -g sickchill "${LOCATION}/bin/pip" install -U "${SICKCHILL_SPEC}" "${INDEXES[@]}"; then
  whiptail --title "Failed to install SickChill" --msgbox "Failed to install SickChill" 8 128
  exit 1
fi

# SysV (init.debian/init.ubuntu) reads PYTHON_BIN from /etc/default/sickchill.
# Upstart execs ${SC_HOME}/SickChill.py. systemd already uses ${LOCATION}/bin/SickChill.
# Update SC_HOME and PYTHON_BIN only; keep SC_DATA, SC_OPTS, and other existing keys.
echo "Updating /etc/default/sickchill with the virtual environment interpreter"
DEFAULTS_FILE=/etc/default/sickchill
DEFAULTS_TMP="${DEFAULTS_FILE}.tmp"
if [[ -f ${DEFAULTS_FILE} ]]; then
  if ! awk -v sc_home="${LOCATION}" -v python_bin="${LOCATION}/bin/python" '
    BEGIN {
      re_home = "^[[:space:]]*SC_HOME="
      re_py = "^[[:space:]]*PYTHON_BIN="
    }
    $0 ~ re_home { print "SC_HOME=\"" sc_home "\""; found_home=1; next }
    $0 ~ re_py { print "PYTHON_BIN=\"" python_bin "\""; found_py=1; next }
    { print }
    END {
      if (!found_home) print "SC_HOME=\"" sc_home "\""
      if (!found_py) print "PYTHON_BIN=\"" python_bin "\""
    }
  ' "${DEFAULTS_FILE}" > "${DEFAULTS_TMP}"; then
    rm -f "${DEFAULTS_TMP}"
    whiptail --title "Failed to write /etc/default/sickchill" --msgbox "Failed to update /etc/default/sickchill" 8 128
    exit 1
  fi
else
  if ! printf '%s\n' \
    '# Generated by debian-ubuntu-install.sh' \
    "SC_HOME=\"${LOCATION}\"" \
    "PYTHON_BIN=\"${LOCATION}/bin/python\"" \
    > "${DEFAULTS_TMP}"; then
    rm -f "${DEFAULTS_TMP}"
    whiptail --title "Failed to write /etc/default/sickchill" --msgbox "Failed to write /etc/default/sickchill" 8 128
    exit 1
  fi
fi
if ! mv "${DEFAULTS_TMP}" "${DEFAULTS_FILE}"; then
  rm -f "${DEFAULTS_TMP}"
  whiptail --title "Failed to write /etc/default/sickchill" --msgbox "Failed to write /etc/default/sickchill" 8 128
  exit 1
fi
if ! chmod 644 "${DEFAULTS_FILE}"; then
  whiptail --title "Failed to set permissions on /etc/default/sickchill" --msgbox "Failed to set permissions on /etc/default/sickchill" 8 128
  exit 1
fi
if ! ln -sf "${LOCATION}/bin/SickChill" "${LOCATION}/SickChill.py"; then
  whiptail --title "Failed to link SickChill.py" --msgbox "Failed to link ${LOCATION}/SickChill.py to the virtual environment entrypoint" 8 128
  exit 1
fi

function download_service_file() {
  export SERVICE_FILE=${2}
  if ! curl -fsSL "https://raw.githubusercontent.com/SickChill/SickChill/master/contrib/runscripts/$1" -o "$2"; then
    whiptail --title "Failed to download ${1}" --msgbox "Failed to download ${1}" 8 128
    exit 1
  fi

  if ! chown root:root "$2" && chmod "$3" "$2"; then
    whiptail --title "Failed to set permissions on ${2}" --msgbox "Failed to set permissions on ${2}" 8 128
    exit 1
  fi
}

# Depending on Distro, copy the service script, then change the owner/group and permissions. Finally start the service
if [[ $(/sbin/init --version 2>/dev/null) =~ upstart ]]; then
  echo "Copying Startup Script To Upstart"
  download_service_file "init.upstart" "/etc/init/sickchill.conf" "644"
  echo "Starting SickChill"
  service sickchill start
elif command -v systemctl >/dev/null 2>&1 && [[ $(systemctl) =~ -\.mount ]]; then
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

SERVICE_RESULT=$?

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
echo "To update sickchill, run the following command as the sickchill user:"
echo ">> sudo -u sickchill -g sickchill ${LOCATION}/bin/pip install -U \"${SICKCHILL_SPEC}\""

if [[ $SERVICE_RESULT != 0 ]]; then
  whiptail --title "Failed to start SickChill" --msgbox "Failed to start SickChill, edit your service file at ${SERVICE_FILE}" 8 128
  echo "Failed to start SickChill, edit your service file at ${SERVICE_FILE}"
  exit 1
fi

# Finish by explaining the script is finished and give them the relevant IP addresses
whiptail --title Complete --msgbox \
"Check that everything has been set up correctly by going to:

          Internal IP: http://${internal_ip}:8081
                             OR
          External IP: http://${external_ip}:8081

 make sure to add sickchill to your download clients group
 and check the log above for information about running sickchill" 15 66
