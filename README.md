# iomt-project
Server part of a project related to the Internet of medical things

    All commands was tested on Linux (Ubuntu-18.04)
## Local installation `make install-local`
> Because of hardcoded MongoDB and ClickHouse integration. 
> Now it is not possible to install and run system fully locally 
> without MongoDB and ClickHouse instances on your PC. 😢 
1. Prepare python virtual environment
   ```shell
   python3.10 -m venv venv
   venv/bin/pip install -r requirements-dev.txt
   ```
2. Fill config file
   ```shell
   cp default_conf.py config/flask_config.py
   ```
   Get your configuration settings for `config/flask_config.py` from your server administrator.

[comment]: <> (2. Install [ClickHouse]&#40;https://clickhouse.com/docs/en/getting-started/install/&#41;)
[comment]: <> (   > **Note**: ClickHouse uses about 1 gigabyte disk space. )
[comment]: <> (   > If you don't want to download ClickHouse write your server )
[comment]: <> (   > data for ClickHouse in config file.)
[comment]: <> (   ```shell)
[comment]: <> (    sudo apt-get install -y apt-transport-https ca-certificates dirmngr)
[comment]: <> (    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD2B48D754)
[comment]: <> (    echo "deb https://packages.clickhouse.com/deb stable main" | sudo tee \ )
[comment]: <> (        /etc/apt/sources.list.d/clickhouse.list)
[comment]: <> (    sudo apt-get update)
[comment]: <> (    sudo apt-get install -y clickhouse-server clickhouse-client)
[comment]: <> (    ```)

3. Install [MongoDB](https://www.mongodb.com/docs/upcoming/tutorial/install-mongodb-on-ubuntu/)
   ```shell
   wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
   echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/5.0 multiverse" | sudo tee \
      /etc/apt/sources.list.d/mongodb-org-5.0.list # !! This command Ubuntu version sensitive !!
   sudo apt-get update
   sudo apt-get install -y mongodb-org
   ```

## Local run

## Server installation

## Server run

--------------------------------

# Possible improvements:
- [ ] Neat logs
- [ ] SQLAlchemy support (maybe with migration to MySQL)
- [ ] RESTful interface

--------------------------------

To start app type in command line:

 • docker build -t jan2801/iomt_01 .
 
 • docker run -p 5000:5000 jan2801/iomt_01

### Mosquitto:

To start Mosquitto:
```
sudo systemctl start mosquitto 
```
To enable Mosquitto:
```
sudo systemctl enable mosquitto
```
To install and add jwt-auth plugin: 

1. Install Rust:
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
2. Clone:
```
git clone git@github.com:wiomoc/mosquitto-jwt-auth.git
```
3. Build:
```
cargo build --release
```
4. Move plugin to /etc/mosquitto/
5. Set enviroment variable ```JWT_KEY```
6. Uncomment strokes in mosquitto.conf

### Flask app

1. Create virtual environment
```
virtualenv .env
source .env/bin/activate
pip3 install -r requirements.txt
deactivate
```
2. Create virtual host config in /etc/nginx/sites-available/ and create symbolic link
```
sudo ln -s /etc/nginx/sites-available/iomt /etc/nginx/sites-enabled
```
3. Create /etc/systemd/system/iomt.service and start service
```
sudo systemctl start iomt
sudo systemctl enable iomt
```
4. Start nginx
```
sudo systemctl start nginx
sudo systemctl enable nginx
```
