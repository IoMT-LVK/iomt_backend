# iomt-project
Server part of a project related to the Internet of medical things


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
