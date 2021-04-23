# iomt-project
Server part of a project related to the Internet of medical things


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

