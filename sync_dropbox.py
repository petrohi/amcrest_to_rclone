#!/var/lib/sftp/sftp_amcrest/venv/bin/python

import os
import sys
import shutil
import toml
import re
import time

def read_config(config_file_name):
    with open(config_file_name, 'r') as config_file:
        return toml.loads(config_file.read())

config = read_config(sys.argv[1])
ffmpeg_concat_list_file = config['daemon']['ffmpeg_concat_list_file'] 
ffmpeg_concat_file = config['daemon']['ffmpeg_concat_file'] 

DATE_REGEX = re.compile('([0-9]{4})-([0-9]{2})-([0-9]{2})')
HOUR_REGEX = re.compile('[0-9]{2}')
MP4_REGEX = re.compile('.+\\.mp4$')
UNFINISHED_MP4_REGEX = re.compile('.+\\.mp4_$')

def scan(camera_name, camera_dir, rclone_remote):
    date_dirs = os.listdir(camera_dir)
    for date_dir in date_dirs:
        date_match = DATE_REGEX.match(date_dir)
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2)
            day = date_match.group(3)
            hours_dir = camera_dir + '/' + date_dir + '/001/dav'
            hour_dirs = os.listdir(hours_dir)
            for hour_dir in hour_dirs:
                if HOUR_REGEX.match(hour_dir):
                    mp4s_dir = hours_dir + '/' + hour_dir
                    mp4s = os.listdir(mp4s_dir)

                    if all(not UNFINISHED_MP4_REGEX.match(mp4) for mp4 in mp4s):
                        print(camera_name + ' confirming: ' + mp4s_dir)
                        time.sleep(60)
                        mp4s = os.listdir(mp4s_dir)
                        mp4s.sort()

                        if all(not UNFINISHED_MP4_REGEX.match(mp4) for mp4 in mp4s):
                            print(camera_name + ' concat: ' + mp4s_dir)
                            with open(ffmpeg_concat_list_file, "w") as mp4_list_file:
                                for mp4 in mp4s:
                                    if MP4_REGEX.match(mp4):
                                        print(camera_name + ' concat file: ' + mp4)
                                        mp4_list_file.write('file \'' + mp4s_dir + '/' + mp4 + '\'\n')

                            os.system('ffmpeg -hide_banner -loglevel error -y -safe 0 -f concat -i /tmp/ffmpeg_concat_list.txt -vcodec copy -acodec copy ' + ffmpeg_concat_file)
                            os.remove(ffmpeg_concat_list_file)

                            if os.path.exists(ffmpeg_concat_file):
                                rclone_path = rclone_remote  + ':' + camera_name + '/' + year + '/' + month + '/' + day + '/' + hour_dir + '.mp4'
                                print(camera_name + ' upload: ' + rclone_path)
                                os.system('rclone copyto ' + ffmpeg_concat_file + ' "' + rclone_path + '"')
                                os.remove(ffmpeg_concat_file)
                            else:
                                print(camera_name + ' bad FFMPEG concat: ' + mp4s_dir)

                            shutil.rmtree(mp4s_dir)
                        else:
                            print(camera_name + ' unfinished: ' + mp4s_dir)
                    else:
                        print(camera_name + ' unfinished: ' + mp4s_dir)

pid_file = config['daemon']['pid_file']
cameras_base_dir = config['cameras']['dir']
rclone_remote = config['rclone']['remote']

def start_daemon():
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
        print('Daemon started.')

def check_running():
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            try:
                pid = int(f.read())
            except:
                print('Bad PID file found, starting a new one.')
                return False
        try:
            os.kill(pid, 0)
            print('Daemon is already running.')
            return True
        except OSError:
            print('No daemon found, starting a new one.')
            return False
    else:
        print('No PID file found, starting a new one.')
        return False

if not check_running():
    start_daemon()
    while True:
        for camera, props in config['cameras'].items():
            if type(props) is dict:
                serial = props['serial']
                scan(camera, cameras_base_dir + '/' + serial, rclone_remote)
        time.sleep(60)