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

# Check to see what SickRage Dependencies are missing
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

# Check to see if sickrage exists; If not make user/group
if [[ ! "$(getent group sickrage)" ]]; then
	echo "Adding SickRage Group"
    	addgroup --system sickrage
fi
if [[ ! "$(getent passwd sickrage)" ]]; then
	echo "Adding SickRage User"
	adduser --disabled-password --system --home /var/lib/sickrage --gecos "SickRage" --ingroup sickrage sickrage
fi

# Check to see if /opt/sickrage exists. If it does ask if they want to overwrite it. if they do not exit 1
# if they do, remove the whole directory and recreate
if [[ ! -d /opt/sickrage ]]; then
	echo "Creating New SickRage Folder"
	mkdir /opt/sickrage && chown sickrage:sickrage /opt/sickrage
	echo "Git Cloning In Progress"
	su -c "cd /opt && git clone -q https://github.com/SickRage/SickRage.git /opt/sickrage" -s /bin/bash sickrage
else
	whiptail --title 'Overwrite?' --yesno "/opt/sickrage already exists, do you want to overwrite it?" 8 40
	choice=$?
	if [[ ${choice} == 0 ]]; then
		echo "Removing Old SickRage Folder And Creating New SickRage Folder"
        	rm -rf /opt/sickrage && mkdir /opt/sickrage && chown sickrage:sickrage /opt/sickrage
		echo "Git Cloning In Progress"
        	su -c "cd /opt && git clone -q https://github.com/SickRage/SickRage.git /opt/sickrage" -s /bin/bash sickrage
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
        cp /opt/sickrage/runscripts/init.upstart /etc/init/sickrage.conf
	chown root:root /etc/init/sickrage.conf && chmod 644 /etc/init/sickrage.conf
	echo "Starting SickRage"
        service sickrage start

    elif [[ $(systemctl) =~ -\.mount ]]; then
    	echo "Copying Startup Script To systemd"
        cp /opt/sickrage/runscripts/init.systemd /etc/systemd/system/sickrage.service
        chown root:root /etc/systemd/system/sickrage.service && chmod 644 /etc/systemd/system/sickrage.service
	echo "Starting SickRage"
        systemctl -q enable sickrage && systemctl -q start sickrage
    else
    	echo "Copying Startup Script To init"
        cp /opt/sickrage/runscripts/init.ubuntu /etc/init.d/sickrage
        chown root:root /etc/init.d/sickrage && chmod 644 /etc/init.d/sickrage
	echo "Starting SickRage"
        update-rc.d sickrage defaults && service sickrage start
    fi
elif [[ ${distro} = debian ]]; then
    if [[ $(systemctl) =~ -\.mount ]]; then
    	echo "Copying Startup Script To systemd"
        cp /opt/sickrage/runscripts/init.systemd /etc/systemd/system/sickrage.service
        chown root:root /etc/systemd/system/sickrage.service && chmod 644 /etc/systemd/system/sickrage.service
	echo "Starting SickRage"
        systemctl -q enable sickrage && systemctl -q start sickrage
    else
    	echo "Copying Startup Script To init"
        cp /opt/sickrage/runscripts/init.debian /etc/init.d/sickrage
        chown root:root /etc/init.d/sickrage && chmod 755 /etc/init.d/sickrage
	echo "Starting SickRage"
        update-rc.d sickrage defaults && service sickrage start
    fi
fi

# Finish by explaining the script is finished and give them the relevant IP addresses
whiptail --title Complete --msgbox "Check that everything has been set up correctly by going to:

          Internal IP: http://$intip:8081
                             OR
          External IP: http://$extip:8081

 make sure to add sickrage to your download clients group" 15 66
