FROM fedora:22
MAINTAINER Pavel Odvody <podvody@redhat.com>

ENV PACKAGES='binwalk cmake findutils file gcc\
              gcc-c++ git libicu-devel make\
              python-pip ruby-devel tar tree\
              which zlib-devel'\
    GEMS='github-linguist'\
    EGGS='redhawk'

RUN dnf install -y ${PACKAGES}\
 && gem install ${GEMS}\
 && pip install ${EGGS}\
 && git config --global user.email "just@something.com"\
 && git config --global user.name "John Foo"

COPY extract-metadata.sh /usr/bin/

CMD ["/bin/bash"]
