#!/usr/bin/env python
import redhawk.common.selector as S
import redhawk.common.get_ast as G
import redhawk.utils.util as U
import redhawk.common.format_position as F
import sys
from os import path, errno

def StringList(lst, sep=', '):
  return sep.join(lst)

class AbstractImport(object):
  def __init__(self, LC):
    self._line = LC[0]
    self._column = LC[1]

  @property
  def line(self):
    return self._line

  @property
  def column(self):
    return self._column


class ImportAs(AbstractImport):
  def __init__(self, LC, A, N):
    super(ImportAs, self).__init__(LC)
    self._aliases = A
    self._name = N

  @property
  def name(self):
    return self._name

  @property
  def aliases(self):
    return self._aliases

  def __repr__(self):
    return "import {0} as {1}".format(self.name, StringList(self.aliases))


class FromImport(AbstractImport):
  def __init__(self, LC, B, I):
    super(FromImport, self).__init__(LC)
    self._base = B
    self._imports = I

  @property
  def base(self):
    return self._base

  @property
  def imports(self):
    return self._imports

  def __repr__(self):
    return "from {0} import {1}".format(self.base, StringList(self.imports))


class Import(AbstractImport):
  def __init__(self, LC, N):
    super(Import, self).__init__(LC)
    self._names = N

  @property
  def imports(self):
    return self._names

  def __repr__(self):
    return "import {0}".format(StringList(self._names))


def Usage(n):
  sys.stdout.write("%s [FILES]\n"%(sys.argv[0]))
  sys.exit(n)

def CompareClass(a, b):
  """ String-typying FTW! """
  return str(a.__class__) == b

def GetPosition(N):
  """ Returns line/column for the given AST node """
  P = F.GetPosition(N)
  return (P.GetLine(), P.GetColumn())

def SelectNodes(A, T):
  """ Selects nodes of particlar type from the tree """
  selector = S.S(node_type=T[1])
  applied = None
  try:
    applied = U.Concat(S.S.Apply(selector, A))
  except:
    pass
  if not applied:
    return []
  return [X for X in applied if CompareClass(X, T[0])]

def ImportFromHandler(tree):
  def _GetModule(N):
    return N.GetAttributes()[1]['module']
  def _GetImported(N):
    def _CreateList(M):
      return M.GetAttributes()[1]['name']
    return map(_CreateList, N.GetAttributes()[1]['import_aliases'])
  imports = []
  for node in SelectNodes(tree, ('redhawk.common.node.ImportFrom', 'ImportFrom')):
    imports.append(FromImport(GetPosition(node), _GetModule(node), _GetImported(node)))
  
  return imports

def ModuleAliasHandler(tree):
  def _GetModule(N):
    M = N.GetAttributes()[1]
    if M['asmodule']:
      return (M['name'], M['asmodule'])
    else:
      return None
  imports = []
  for node in SelectNodes(tree, ('redhawk.common.node.ModuleAlias', 'ModuleAlias')):
    M = _GetModule(node)
    if M:
      imports.append(ImportAs(GetPosition(node), M[1], M[0]))

  return imports

def ImportHandler(tree):
  imports =[]
  for node in SelectNodes(tree, ('redhawk.common.node.Import', 'Import')):
    """ `import X` and `import X as Y` both descend from the same `import` node """
    if not node.import_aliases[0].asmodule:
      imports.append(Import(GetPosition(node), [x.name for x in node.import_aliases]))

  return imports

def Main():
  if len(sys.argv) < 2:
    Usage(1)
  if "-h" in sys.argv:
    Usage(0)

  files = sys.argv[1:]

  asts = [G.GetLAST(x, database = None, key = 'python') for x in files]

  print StringList((str(x) for x in ImportFromHandler(asts)), sep='\n')
  print StringList((str(x) for x in ModuleAliasHandler(asts)), sep='\n')
  print StringList((str(x) for x in ImportHandler(asts)), sep='\n')

  return

if __name__ == '__main__':
  Main()
