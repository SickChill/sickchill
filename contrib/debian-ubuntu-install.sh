#!/bin/bash --
# Author: @DirtyCajunRice

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
    extip=$(curl -s ${i})
    [[ ! ${extip} ]] || break
done

# Get internal ip address
intip=$(ip r g 8.8.8.8 | awk 'NR==1{print $7};')

# Installed whiptail for script prerequisite
apt-get -qq install whiptail -y

# Check to see what SickChill Dependencies are missing
packages=$(dpkg -l unrar-free git-core openssl libssl-dev python2.7 2>1 | grep "no packages" | \
           awk '{ print $6 }' | tr '\n' ' ')
if [[ ${packages} ]]; then
# Show Whiptail and install required files
    {
    i=1
    while read -r line; do
        i=$(( $i + 1 ))
        echo ${i}
    done < <(apt-get update && apt-get install ${packages} -y)
    } | whiptail --title "Progress" --gauge "Installing $packages" 8 80 0
fi
# Check to see if all prior packages were installed successfully. if not exit 1 and display whiptail issues

if [[ $(dpkg -l unrar-free git-core openssl libssl-dev python2.7 2>&1 | grep "no packages" | \
        awk '{print $6 }') ]]; then
    whiptail --title "Package Installation Failed" --msgbox "               These Packages have failed:
               $(dpkg -l unrar-free git-core openssl libssl-dev python2.7 2>&1 | grep "no packages" | awk '{print $6 }')
Please resolve these issues and restart the install script" 15 66
exit 1
fi

# Check to see if sickchill exists; If not make user/group
if [[ ! "$(getent group sickchill)" ]]; then
	echo "Adding SickChill Group"
    	addgroup --system sickchill
fi
if [[ ! "$(getent passwd sickchill)" ]]; then
	echo "Adding SickChill User"
	adduser --disabled-password --system --home /var/lib/sickchill --gecos "SickChill" --ingroup sickchill sickchill
fi

# Check to see if /opt/sickchill exists. If it does ask if they want to overwrite it. if they do not exit 1
# if they do, remove the whole directory and recreate
if [[ ! -d /opt/sickchill ]]; then
	echo "Creating New SickChill Folder"
	mkdir /opt/sickchill && chown sickchill:sickchill /opt/sickchill
	echo "Git Cloning In Progress"
	su -c "cd /opt && git clone -q https://github.com/SickChill/SickChill.git /opt/sickchill" -s /bin/bash sickchill
else
	whiptail --title 'Overwrite?' --yesno "/opt/sickchill already exists, do you want to overwrite it?" 8 40
	choice=$?
	if [[ ${choice} == 0 ]]; then
		echo "Removing Old SickChill Folder And Creating New SickChill Folder"
        	rm -rf /opt/sickchill && mkdir /opt/sickchill && chown sickchill:sickchill /opt/sickchill
		echo "Git Cloning In Progress"
        	su -c "cd /opt && git clone -q https://github.com/SickChill/SickChill.git /opt/sickchill" -s /bin/bash sickchill
    	else
        	echo
        	exit 1
    	fi
fi

# Depending on Distro, Cp the service script, then change the owner/group and change the permissions. Finally
# start the service
if [[ ${distro} = ubuntu ]]; then
    if [[ $(/sbin/init --version 2> /dev/null) =~ upstart ]]; then
    	echo "Copying Startup Script To Upstart"
        cp /opt/sickchill/runscripts/init.upstart /etc/init/sickchill.conf
	chown root:root /etc/init/sickchill.conf && chmod 644 /etc/init/sickchill.conf
	echo "Starting SickChill"
        service sickchill start

    elif [[ $(systemctl) =~ -\.mount ]]; then
    	echo "Copying Startup Script To systemd"
        cp /opt/sickchill/runscripts/init.systemd /etc/systemd/system/sickchill.service
        chown root:root /etc/systemd/system/sickchill.service && chmod 644 /etc/systemd/system/sickchill.service
	echo "Starting SickChill"
        systemctl -q enable sickchill && systemctl -q start sickchill
    else
    	echo "Copying Startup Script To init"
        cp /opt/sickchill/runscripts/init.ubuntu /etc/init.d/sickchill
        chown root:root /etc/init.d/sickchill && chmod 644 /etc/init.d/sickchill
	echo "Starting SickChill"
        update-rc.d sickchill defaults && service sickchill start
    fi
elif [[ ${distro} = debian ]]; then
    if [[ $(systemctl) =~ -\.mount ]]; then
    	echo "Copying Startup Script To systemd"
        cp /opt/sickchill/runscripts/init.systemd /etc/systemd/system/sickchill.service
        chown root:root /etc/systemd/system/sickchill.service && chmod 644 /etc/systemd/system/sickchill.service
	echo "Starting SickChill"
        systemctl -q enable sickchill && systemctl -q start sickchill
    else
    	echo "Copying Startup Script To init"
        cp /opt/sickchill/runscripts/init.debian /etc/init.d/sickchill
        chown root:root /etc/init.d/sickchill && chmod 755 /etc/init.d/sickchill
	echo "Starting SickChill"
        update-rc.d sickchill defaults && service sickchill start
    fi
fi

# Finish by explaining the script is finished and give them the relevant IP addresses
whiptail --title Complete --msgbox "Check that everything has been set up correctly by going to:

          Internal IP: http://$intip:8081
                             OR
          External IP: http://$extip:8081

 make sure to add sickchill to your download clients group" 15 66
