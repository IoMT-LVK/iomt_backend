# Install MongoDB
install-mongo:
	wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
	echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/5.0 multiverse" | sudo tee \
      /etc/apt/sources.list.d/mongodb-org-5.0.list # !! This command Ubuntu version sensitive
	sudo apt-get update
	sudo apt-get install -y mongodb-org

# Uninstall MongoDB
uninstall-mongo:
	#sudo service mongod stop || sudo systemctl stop mongod # depends on your init system (this is for System V, for systemd check official site)
	sudo apt-get purge mongodb-org*
	sudo rm -r /var/log/mongodb
	sudo rm -r /var/lib/mongodb  # !! Caution: removes all databases


install-local:
	# Install python dependencies
	python3.10 -m venv venv
	venv/bin/pip install -r requirements-dev.txt

	# Fill your database and mail credit data in config/flask_config.py
	cp default_conf.py config/flask_config.py

#	# Install ClickHouse
#	sudo apt-get install -y apt-transport-https ca-certificates dirmngr
#	sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD2B48D754
#	echo "deb https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list
#	sudo apt-get update
#	sudo apt-get install -y clickhouse-server clickhouse-client
