#!/bin/fish

source .venv/bin/activate.fish

# USB mount example
mkdir -p /mnt/USB
mount /dev/sdb1 /mnt/USB
chown -R user /mnt/USB

# Run the server at your IP
python manage.py runserver 192.168.100.4:8000