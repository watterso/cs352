class Scope:
  def __init__(self, parent=None, **kwargs):
    self.parent = parent
    self.scope = {}.update(kwargs)

  def _find(self, var):
    s = self
    while(s):
      if s.scope.contains(var):
        return (s, s.scope[var])
      s = s.parent
    return None

  def exists(self, var):
    return self._find(var) ? True : False

  def defined(self, var):
    return self.exists(var) && self._find(var)[1] != None

  def get_var(self, var):
    res = self._find(var)
    if res:
      return res[1]
    else:
      #TODO throw access error
      return None

  def set_vars(self, a_dict):
    for key, val in a_dict:
      self.set_var(key, val)
  
  def set_var(self, var, val=None, recurse=True):
    was_set = False
    if recurse:
      res = self._find(var)
      if res:
        res[0].set_var(var, val, False)
      else:
        self.scope[var] = val
    else:
      self.scope[var] = val

class Node:
  def __init__(self, before=None, after=None):
    self.before = before
    self.after = after
    self.stmts = []
    init_scope()

  def exe(self):
    for s in self.stmts:
      s.exe(self.scope)

  def init_scope(self):
    if before && before.scope:
      self.scope = Scope(parent = before.scope) 
    else:
      self.scope = Scope()

class IfNode(Node):
  def __init__(self, cond, soit=None, before=None, after=None):
    super(before, after)
    self.cond = cond
    self.soit = soit

  def exe(self): 
    if cond.exe():
      self.exe()
    else:
      self.soit.exe()

class Statement:
  pass

class Decl(Statement):
  def __init__(self, var):
    self.var = var

  def exe(self, scope):
    scope.set_var(self.var, None, recurse=False)

class Init(Statement):
  def __init__(self, var, val):
    self.var = var
    self.val = val
    
  def exe(self, scope):
    scope.set_var(self.var, self.val, recurse=False)

class Assign(Statement):
  def __init__(self, var, val):
    self.var = var
    self.val = val

  def exe(self, scope):
    if scope.exists(self.var):
      scope.set_var(self.var, self.val)
    else:
      #TODO no such variable error
      # (we assign it anyway)
      scope.set_var(self.var, self.val)
