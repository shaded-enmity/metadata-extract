import redhawk.common.selector as S
import redhawk.common.get_ast as G
import redhawk.utils.util as U
import os, sys, pprint

def process(target, outpath='./'):
  target_dir = target
  settings_py = None

  # search recursively for settings.py
  for root, _, files in os.walk(target_dir):
    for f in files:
      if f == 'settings.py':
        settings_py = os.path.join(root, f)
  if not settings_py:
    print("=> unable to find settings.py")
    sys.exit(1)

  print("=> django settings.py found: {0}".format(settings_py))

  asts = [G.GetLAST(x, database = None) for x in [settings_py]]
  # figure out if the file imports os module already
  # if it doesn't it'll have to be injected so that
  # we can call the `getenv` function
  selector = S.S(node_type = 'ModuleAlias',
               function = lambda x: x.name == 'os')
  has_os_module = next(selector.Apply(asts), None)
  selector = S.S(node_type = 'Assignment',
               function = lambda x: x.lvalue.name == 'DATABASES')
  variables = U.Concat(selector.Apply(asts))
  
  # variables are returned in the form:
  # (Assignment, Module, Assigment, Module ...)
  #
  # so we skip every even node, but there should be
  # single assignment anyway
  for f in variables[::2]:
    N = f.rvalue
    if N.keys[0].value == 'default':
      DICT = dict(default=dict())
      print("==> patching")
      Dx = DICT['default']
      Dx['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
      Dx['PORT'] = 'os.getenv(\'DB_PORT\')'
      Dx['HOST'] = 'os.getenv(\'DB_HOST\')'
      Dx['USER'] = 'os.getenv(\'DB_USER\')'
      Dx['PASSWORD'] = 'os.getenv(\'DB_PASSWORD\')'
      Dx['NAME'] = 'os.getenv(\'DB_NAME\')'
      Dx['PATH'] = settings_py
      L = [x.replace('"', '') + '\n' for x in pprint.pformat(DICT).splitlines()]
      # prepend the variable assignement to the first line
      L[0] = 'DATABASES=' + L[0]
      if not has_os_module:
        print(" => import os module will be injected")
      print("==> patching done")
      # figure out which lines in the original source file
      # we'll be replacing with our updated configuration
      ST = f.position.GetLine()
      DT = sorted(list(set([x.position.GetLine() for x in f.GetParent().GetChildren()])))
      IX = DT.index(ST)
      if IX != (len(DT) - 1):
        # last line is on the next node
        EXT = (ST, DT[IX + 1])
      else:
        # last line is the last line of the file
        EXT = (ST, -1)
      print "=> dictionary extents ({0}, {1})".format(*EXT)
      with open(settings_py, 'r') as st:
        lines = st.readlines()
        if not has_os_module:
          # add import os on top of the file
          Sl =  ['import os\n'] + lines[1:EXT[0] - 1]
          #Sl =  ['import os\n'] + [lines[0]] + lines[1:EXT[0] - 1]
        else:
          Sl = lines[:EXT[0] - 1]
        if EXT[1] == -1:
          EXT[1] = len(lines)
        El = lines[EXT[1] - 2:]
        PATH = os.path.join(outpath, 'settings.py')
        with open(PATH, 'w+') as ot:
          ot.writelines(Sl + L + El)
      print("=> file {0}.deploy written".format(PATH))
      return Dx

  return None
