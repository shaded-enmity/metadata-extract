#!/usr/bin/python
import redhawk.common.selector as S
import redhawk.common.get_ast as G
import redhawk.utils.util as U
import os, sys, pprint

def Usage(rc):
  print('necum')
  sys.exit(rc)

def Main():
  if len(sys.argv) < 2:
    Usage(1)
  if "-h" in sys.argv:
    Usage(0)

  target_dir = sys.argv[1]
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
      # second child is the dictionary
      D = N.GetChildren()[1][0]
      DICT = dict(default=dict(
          # create tuples from the zipped key and value sequences  
          # so that we can easily convert to dict
          map(lambda (k, v): (k, v), 
            zip([x.value for x in D.keys], [x.value for x in D.values])
          )
      ))
      print("==> database settings:")
      pprint.pprint(DICT)
      print("==> patching")
      Dx = DICT['default']
      Dx['PORT'] = 'os.getenv(\'DB_PORT\')'
      Dx['HOST'] = 'os.getenv(\'DB_HOST\')'
      Dx['USER'] = 'os.getenv(\'DB_USER\')'
      Dx['PASSWORD'] = 'os.getenv(\'DB_PASSWORD\')'
      Dx['NAME'] = 'os.getenv(\'DB_NAME\')'
      L = [x.replace('"', '') + '\n' for x in pprint.pformat(DICT).splitlines()]
      # prepend the variable assignement to the first line
      L[0] = 'DATABASES=' + L[0]
      if not has_os_module:
        print(" => import os module will be injected")
      print("==> patching done")
      # figure out which lines in the original source file
      # we'll be replacing with our updated configuration
      EXT = (f.position.GetLine(), 
              max([x.position.GetLine() for x in f.GetParent().GetChildren()]))
      print "=> dictionary extents ({0}, {1})".format(*EXT)
      with open(settings_py, 'r') as st:
        lines = st.readlines()
        if not has_os_module:
          Sl = [lines[0]] + ['import os\n'] + lines[1:EXT[0] - 1]
        else:
          Sl = lines[:EXT[0] - 1]
        El = lines[EXT[1] - 2:]
        with open(settings_py + '.nulecule', 'w+') as ot:
          ot.writelines(Sl + L + El)
      print("=> file {0}.nulecule written".format(settings_py))

  return

if __name__ == '__main__':
  Main()
