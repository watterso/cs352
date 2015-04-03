def is_array(a_dict):
  return not False in [type(k) is int for k in a_dict.keys()]

def _exe_stmts(stmts):
  for s in stmts:
    s.exe()

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
    return True if self._find(var) else False

  def defined(self, var):
    return self.exists(var) and self._find(var)[1] != None

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

  def set_var(self, var, val=None, field=None, recurse=True):
    was_set = False
    if recurse:
      res = self._find(var)
      if res:
        res[0].set_var(var, val, field, False)
      else:
        if field:
          self.scope[var][field] = val
        else:
          self.scope[var] = val
    else:
      if field:
        self.scope[var][field] = val
      else:
        self.scope[var] = val

class Var:
  def __init__(self, key, scope, field=None):
    self.key = key
    self.field = field
    self.scope = scope

  def get(self):
    if self.field:
      return self.scope.get(key)[field]
    else:
      return self.scope.get(key)

class Node:
  def __init__(self, before, after=None):
    self.before = before
    self.after = after
    self.stmts = []
    self.init_scope()

  def exe(self):
    for s in self.stmts:
      s.exe(self.scope)

  def init_scope(self):
    if self.before and self.before.scope:
      self.scope = Scope(parent = self.before.scope) 
    else:
      self.scope = Scope()

  def append(statement):
    self.stmts.append(statement)

  def extend(statements):
    self.stmts.extend(statements)

class Statement:
  def exe(self, **kwargs):
    pass

class Block(Statement):
  def __init__(self, stmts):
    self.stmts = stmts

  def exe(self):
    _exe_stmts(self.stmts)

class If(Statement):
  def __init__(self, cond, stmts, soit=None):
    self.cond = cond
    self.soit = soit
    self.stmts = stmts

  def exe(self): 
    if cond.exe():
      _exe_stmts(self.stmts)
    elif soit is not None:
      self.soit.exe()

class WhileNode(Statement):
  def __init__(self, cond, stmts):
    self.cond = cond
    self.stmts = stmts 

  def exe(self):
    while cond.exe():
      _exe_stmts(self.stmts)
      
class DoWhileNode(Node):
  def __init__(self, cond, stmts):
    self.cond = cond
    self.stmts = stmts 

  def exe(self):
    _exe_stmts(self.stmts)
    while cond.exe():
      _exe_stmts(self.stmts)


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
  def __init__(self, var, val, field=None):
    self.var = var
    self.val = val
    self.field = field

  def exe(self, scope):
    if scope.exists(self.var):
      scope.set_var(self.var, self.val, self.field)
    else:
      #TODO no such variable error
      # (we assign it anyway)
      scope.set_var(self.var, self.val, self.field)

class Op(Statement):
  def __init__(self, func, *kwargs):
    self.func = func
    self.kwargs = kwargs

  def exe(self, scope):
    return self.func(scope, self.kwargs)

def render_vars(func):
  def render():
    if isinstance(lval, Var):
      lval = lval.get()
    if isinstance(rval, Var):
      rval = rval.get()
    func()
  return render

@render_vars
def And(lval, rval):
  return lval and rval

@render_vars
def Or(lval, rval):
  return lval or rval

def Not(val):
  if isinstance(val, Var):
    val = val.get()
  return not val

@render_vars
def GTE(lval, rval):
  return lval >= rval

@render_vars
def LTE(lval, rval):
  return lval <= rval

@render_vars
def GT(lval, rval):
  return lval > rval

@render_vars
def LT(lval, rval):
  return lval < rval

@render_vars
def EQ(lval, rval):
  return lval == rval

@render_vars
def NE(lval, rval):
  return lval != rval

@render_vars
def Add(lval, rval):
  #TODO type check?
  return lval + rval

@render_vars
def Sub(lval, rval):
  #TODO type check?
  return lval - rval

@render_vars
def Mult(lval, rval):
  #TODO type check?
  return lval * rval

@render_vars
def Div(lval, rval):
  #TODO type check?
  return lval / rval
