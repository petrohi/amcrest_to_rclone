# Automatic upload of Amcrest media to Dropbox

## Setup

### 1. Install Python, FFMPEG and rclone
```
sudo apt update
sudo apt upgrade
sudo apt install python3-venv ffmpeg rclone
```
### 2. Setup `sftp` group, `sftp_amcrest` user, its password, and configure `sshd` server
```
sudo mkdir /var/lib/sftp
sudo groupadd sftp
sudo useradd --base-dir /var/lib/sftp --create-home -g sftp sftp_amcrest
sudo passwd sftp_amcrest
sudo bash -c 'cat <<EOF >> /etc/ssh/sshd_config
Match group sftp
ChrootDirectory /var/lib/sftp
X11Forwarding no
AllowTcpForwarding no
ForceCommand internal-sftp
EOF'
sudo systemctl restart ssh
```
### 3. Setup camera
3.1 Set camera video settings to H.265 and 720P
![camera_video](/doc/camera_video.png)
3.2 Set desired recording schedule
![storage_record_schedule](/doc/storage_record_schedule.png)
3.3 Set storage recording destination path to FTP
![storage_record_destination](/doc/storage_record_destination.png)
3.4 Set SFTP settings
![storage_record_destination_ftp](/doc/storage_record_destination_ftp.png)
3.5 Take note of camera serial number (S/N)
![information_version](/doc/information_version.png)
### 4. Setup sync cron job
4.1 Login as `sftp_amcrest`
```
sudo -u sftp_amcrest bash
cd
```
4.2 Install latest `amcrest_to_dropbox` release
```
export TAG=0.0.5
wget https://github.com/petrohi/amcrest_to_dropbox/archive/refs/tags/${TAG}.tar.gz
tar xf ${TAG}.tar.gz
mv amcrest_to_dropbox-${TAG}/*.py .
mv amcrest_to_dropbox-${TAG}/*.toml .
mv amcrest_to_dropbox-${TAG}/*.txt .
rm -r ${TAG}.tar.gz amcrest_to_dropbox-${TAG}/
python3 -m venv ~/venv
~/venv/bin/pip install -r 
rm requirements.txt
```
4.3 Configure rclone
```
rclone config
```
4.4 Test sync
```
~/sync_dropbox.py ~/sync_dropbox.toml
```
4.5 Setup cron job
```
crontab -e
```
Paste folowing line at the end of edited file
```
15 * * * * ~/sync_dropbox.py ~/sync_dropbox.toml >> ~/sync_dropbox.log 2>&1
```