#!/usr/bin/python -tt
import argparse
import docker
import json
import os
import random
import shutil
import stat
import string
import sys
import tempfile
import targets.django_postgres as django_postgres_handler

DJANGO_DBS=['django.db.backends.postgresql_psycopg2']
DB_IMAGES={
  'postgresql_psycopg2': 'postgres',
  'mysql': 'mariadb',
  'sqlite3': None
}

def get_database_image(db):
  """ Get container image for database """

  rest, type = db.rsplit('.', 1)
  if type in DB_IMAGES:
    return DB_IMAGES[type]

  return None

def gen_name():
  """ Generate random particle name """

  PREFIXES = [
    'pr', 'er', 'ba', 'r', 'ir', 'br', 'as', 'es', 'gr',
    'ar', 'is', 'ur', 'ap', 'ep', 'us', 'an', 'ip', 'ut',
    'am', 'im', 'uj', 'ak', 'phi', 'uk', 'or', 'pha', 'ul',
    'op', 'phe', 'xu', 'on', 'tra', 'xer'
  ]
  SUFFIXES = [
    'on', 'om', 'ion', 'tum', 'yon', 'ytum', 'ton', 'ium'
  ]

  return random.choice(PREFIXES) + random.choice(SUFFIXES)

def gen_str(size=6, chars=string.ascii_uppercase + string.digits):
  """ Generate random combination of `chars` of certain `size` """

  return ''.join(random.choice(chars) for _ in range(size))

def parse_args():
  """ Parse common arguments """

  ap = argparse.ArgumentParser()
  ap.add_argument('-t', '--type', help='Type of the application to deploy', default=None)
  ap.add_argument('-p', '--provision', help='command to execute before the source is copied to the image')
  ap.add_argument('target', help='Django project directory')

  return ap.parse_args()

def create_cache(path):
  """ Create and populate build cache from `path` """

  cache = tempfile.mkdtemp()
  print("==> creaing application build cache: {0}".format(cache))
  # copytree creates the dir and fails if it exists
  os.rmdir(cache)
  shutil.copytree(path, cache)
  os.mkdir(os.path.join(cache, '.deploybits'))

  return cache

def replace_database_settings(original, original_path, indir):
  """ Replace database settings with auto-generated ones """

  relative_settings = os.path.relpath(original, original_path)
  sf = os.path.join(indir, os.path.dirname(relative_settings), 'settings.py')
  os.remove(sf)
  source = os.path.join(indir, '.deploybits', 'settings.py')
  shutil.copy(source, sf)

  return source

def create_dockerfile(indir, settings):
  """ Creates Dockerfile in target directory `indir` from `settings` """

  path = os.path.join(indir, 'Dockerfile')
  with open(path, 'w') as df:
    df.write("FROM {0}\n".format(settings['image']))
    if 'provision' in settings:
      # install additional packages etc.
      df.write("RUN {0}\n".format(settings['provision']))
    df.write("COPY . {1}\n".format(settings['relative_source'], settings['image_target_dir']))
    df.write("WORKDIR {0}\n".format(settings['image_target_dir']))
    df.write("EXPOSE 8080\n")
    if 'img_cmd' in settings:
      # override entrypoint/cmd
      df.write("CMD [\"{0}\"]\n".format(settings['img_cmd']))
  return path

def create_settings(indir, settings):
  pass

def create_deployfile(indir, settings):
  """ Create executable `deployfile` """

  dbimg = get_database_image(settings['database']['ENGINE'])
  user, pw, name = gen_str(8), gen_str(8), gen_name()
  f = os.path.join(indir, 'deployfile')

  with open(f, "w") as df:
    df.write('#!/usr/bin/bash\n\n')
    df.write('DPL_NAME=${{2:-{0}}}\n\n'.format(name))
    df.write('function start() {\n')
    df.write('  DB=$(docker run -d -e POSTGRES_USER="{0}" -e POSTGRES_PASSWORD="{1}" -P' 
             ' --name="${{DPL_NAME}}_db" {2})\n'.format(user, pw, dbimg))
    df.write('  sleep 5\n')
    df.write('  APP=$(docker run -d -e DB_LINK="${{DPL_NAME}}_DB" -e DB_USER="{0}" -e' 
             ' DB_PASSWORD="{1}" -P --name="$DPL_NAME" --link="${{DPL_NAME}}_db" {2})\n'
             ''.format(user, pw, settings['django_image_name']))
    df.write('  echo "=> $DPL_NAME started"\n')
    df.write('  printf "http://127.0.0.1:%s\\n" $(docker inspect --format \'{{' 
             ' .NetworkSettings.Ports }}\' $APP | sed -e \'s/.*\ \([0-9]*\).*/\\1/g\')\n')
    df.write('}\n\n')
    df.write('function stop() {\n')
    df.write('  1>/dev/null 2>&1 docker rm -f ${DPL_NAME}_db ${DPL_NAME} && echo "=> $DPL_NAME stopped"\n')
    df.write('}\n\n')
    df.write('function cleanup() {\n')
    df.write('  stop ; docker rmi -f {0} 1>/dev/null && echo "=> image {0} removed"\n'.format(settings['django_image_name']))
    df.write('}\n\n')
    df.write('eval ${1}\n')

  st = os.stat(f)
  os.chmod(f, st.st_mode | stat.S_IEXEC)

  return f, name

def django_handler(path):
  print("=> django processing '{0}'".format(path))

  if 'manage.py' not in os.listdir(path):
    raise Exception('Path "{0}" is not a valid Django project'.format(
      os.path.abspath(path)))

  build_cache = create_cache(path)

  database = django_postgres_handler.process(path, os.path.join(build_cache, '.deploybits'))
  settings = {'type': "django", 'image': "django", 
      'relative_source': path, 'image_target_dir': "/django/source_dir", 
      'img_cmd': "/django/source_dir/django-deploy" 
  }

  if not database or database['ENGINE'] not in DJANGO_DBS:
    raise Exception("No database to deploy")

  if settings:
    replaced = replace_database_settings(database['PATH'], path, build_cache)

    shutil.copy('guest/django-deploy', build_cache)
    dockerfile = create_dockerfile(build_cache, settings)
    print("==> created Dockerfile: {0}".format(dockerfile))

    tag = 'nulecule:{0}-{1}'.format(os.path.basename(os.path.split(path)[0]), 
                                    os.path.basename(build_cache))

    d = docker.Client()
    print("=> established connection with Docker")

    print('=> building Django image "{0}"'.format(tag))
    for msg in d.build(path=build_cache, tag=tag, rm=True, pull=False):
      print("> {0}".format(json.loads(msg)['stream'].strip()))
    print('=> image built!')

    df, name = create_deployfile(os.getcwd(), {
      'django_image_name': tag,
      'database': database
    })

    print('==> created deployfile "{0}" for Nulecule app "{1}"'.format(df, name))
    print('=> cleaning up "{0}"'.format(build_cache))
    shutil.rmtree(build_cache)
    print('=> execute: \'./deployfile start\' in current directory to start the application')
  else:
    raise Exception("No settings")

args = parse_args()

deployment = {
  'django': django_handler,
}.get(args.type, None)

if deployment:
  deployment(args.target)
