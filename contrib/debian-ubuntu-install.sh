#!/bin/bash --
# Author: @DirtyCajunRice

if [[ $UID -ne 0 ]]; then
	echo 'Script must be run as root'
	exit 0
fi

if [[ $(cat /etc/issue) =~ Debian ]]; then
	distro=debian
elif [[ $(cat /etc/issue) =~ Ubuntu ]]; then
	distro=ubuntu
else
	echo "This script will only work on Debian and Ubuntu Distros, but you are using $(cat /etc/issue)"
	exit 0
fi

for i in 'ipecho.net/plain' 'ifconfig.me' 'checkip.amazonaws.com'; do
extip=$(curl -s $i)
[[ ! $extip ]] || break
done

intip=$(ip r g 8.8.8.8 | awk '{print $7};' | head -n1)

if [[ ! $extip ]]; then
	echo "This script requires a stable internet connection"
fi

apt-get -qq install whiptail -y

{
i=1
    while read -r line; do
		i=$(( $i + 1 ))
        echo $i
    done < <(apt-get update && apt-get install unrar-free git-core openssl libssl-dev whiptail python2.7 -y)
} | whiptail --title "Progress" --gauge "
   Installing unrar-free, git-core, openssl, libssl-dev, and python2.7" 8 80 0

if [[ ! "$(getent group sickrage)" ]]; then
	addgroup --system sickrage
fi
if [[ ! "$(getent passwd sickrage)" ]]; then
	adduser --disabled-password --system --home /var/lib/sickrage --gecos "SickRage" --ingroup sickrage sickrage
fi

if [[ ! -d /opt/sickrage ]]; then
	mkdir /opt/sickrage && chown sickrage:sickrage /opt/sickrage
else
	rm -rf /opt/sickrage && mkdir /opt/sickrage && chown sickrage:sickrage /opt/sickrage
fi

su -c "git clone https://github.com/SickRage/SickRage.git /opt/sickrage" -s /bin/bash sickrage

if [[ $distro = ubuntu ]]; then
	if [[ $(/sbin/init --version 2> /dev/null) =~ upstart ]]; then

		cp /opt/sickrage/runscripts/init.upstart /etc/init/sickrage.conf
		
		chown root:root /etc/init/sickrage.conf
		chmod 644 /etc/init/sickrage.conf
		
		service sickrage start
		
	elif [[ $(systemctl) =~ -\.mount ]]; then
		
		cp /opt/sickrage/runscripts/init.systemd /etc/systemd/system/sickrage.service

		chown root:root /etc/systemd/system/sickrage.service
		chmod 644 /etc/systemd/system/sickrage.service

		systemctl -q enable sickrage
		systemctl -q start sickrage
	else
		cp /opt/sickrage/runscripts/init.ubuntu /etc/init.d/sickrage
		
		chown root:root /etc/init.d/sickrage
		chmod 644 /etc/init.d/sickrage
		
		update-rc.d sickrage defaults
		service sickrage start
	fi
elif [[ $distro = debian ]]; then
	if [[ $(systemctl) =~ -\.mount ]]; then
		
		cp /opt/sickrage/runscripts/init.systemd /etc/systemd/system/sickrage.service

		chown root:root /etc/systemd/system/sickrage.service
		chmod 644 /etc/systemd/system/sickrage.service

		systemctl -q enable sickrage
		systemctl -q start sickrage
	else
		cp /opt/sickrage/runscripts/init.debian /etc/init.d/sickrage
		
		chown root:root /etc/init.d/sickrage
		chmod 644 /etc/init.d/sickrage
		
		update-rc.d sickrage defaults
		service sickrage start
	fi
fi

whiptail --title Complete --msgbox \ "Check that everything has been set up correctly by going to:
     
          Internal IP: http://$intip:8081
                             OR
          External IP: http://$extip:8081

 make sure to add sickrage to your download clients group" 15 66
