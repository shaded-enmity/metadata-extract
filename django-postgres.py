#!/usr/bin/python

import os, sys

target_dir = sys.argv[1]
settings_py = None
for root, _, files in os.walk(target_dir):
  for f in files:
    if f == 'settings.py':
      settings_py = os.path.join(root, f)
print("=> django module found: {0}".format(settings_py))

setmod = compile(open(settings_py).read(), settings_py, 'exec')
exec(setmod)

print("==> database settings:")
for (name, settings) in DATABASES.iteritems():
  print(name + " : " + str(settings))
