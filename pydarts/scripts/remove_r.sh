#!/bin/sh

cat /pydarts/scripts/Backup.sh | tr -d '\r' > /pydarts/scripts/BackupNew.sh

rm /pydarts/scripts/Backup.sh

mv /pydarts/scripts/BackupNew.sh /pydarts/scripts/Backup.sh

chmod +x /pydarts/scripts/Backup.sh

cat /pydarts/scripts/Intro.sh | tr -d '\r' > /pydarts/scripts/IntroNew.sh

rm /pydarts/scripts/Intro.sh

mv /pydarts/scripts/IntroNew.sh /pydarts/scripts/Intro.sh

chmod +x /pydarts/scripts/Intro.sh
