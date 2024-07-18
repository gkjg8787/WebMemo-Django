FROM debian:bookworm

RUN apt-get update

RUN apt-get install -y tzdata
ENV TZ=Asia/Tokyo
RUN ln -sf /usr/share/zoneinfo/Japan /etc/localtime && \
    echo $TZ > /etc/timezone
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8


RUN apt-get install -y python3

RUN apt-get install -y \
    python3-pip sqlite3 python3-venv

WORKDIR /app

COPY requirements.txt ./

RUN python3 -m venv /app/venv && . /app/venv/bin/activate && pip install -Ur requirements.txt

ENV PATH /app/venv/bin:$PATH

COPY . .

EXPOSE 8000

WORKDIR /app/mysite

RUN python manage.py migrate && python manage.py makemigrations webmemo && python manage.py migrate

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
