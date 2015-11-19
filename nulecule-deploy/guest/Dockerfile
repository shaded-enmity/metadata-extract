FROM fedora:22
MAINTAINER Pavel Odvody <podvody@redhat.com>

RUN dnf install -y python-django postgresql-devel python-psycopg2

COPY django-deploy /usr/bin/

CMD ["bash"]
