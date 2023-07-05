
From python:3.9.0b4-alpine3.12


copy requirements.txt  .
copy root /var/spool/cron/crontabs/root
copy main.py /bin/main.py

RUN pip install -r requirements.txt
RUN chmod +x bin/main.py
CMD crond -l 2 -f



