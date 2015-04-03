from __future__ import print_function
import copy
import json


def is_array(a_dict):
  return not False in [type(k) is int for k in a_dict.keys()]

def _exe_stmts(stmts, scope):
  for s in stmts:
    if s:
      s.exe(scope)

class Scope:
  def __init__(self, parent=None, **kwargs):
    self.parent = parent
    self.scope = {}
    self.scope.update(kwargs)

  def __str__(self):
    return json.dumps(self.scope, indent=2)

  def _find(self, var):
    s = self
    while(s):
      if var in s.scope:
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
        if field is not None:
          self.scope[var][field] = val
        else:
          self.scope[var] = val
    else:
      if field is not None:
        self.scope[var][field] = val
      else:
        self.scope[var] = val

class Statement:
  def exe(self, scope):
    pass

class Block(Statement):
  def __init__(self, stmts=[]):
    self.stmts = stmts

  def exe(self, scope):
    _exe_stmts(self.stmts, scope)

class If(Statement):
  def __init__(self, cond, stmts, soit=None):
    self.cond = cond
    self.soit = soit
    self.stmts = stmts

  def exe(self, scope): 
    if self.cond.exe(scope):
      _exe_stmts(self.stmts, scope)
    elif self.soit is not None:
      self.soit.exe(scope)

class While(Statement):
  def __init__(self, cond, stmts):
    self.cond = cond
    self.stmts = stmts 

  def exe(self, scope):
    while self.cond.exe(scope):
      _exe_stmts(self.stmts, scope)
      
class DoWhile(Statement):
  def __init__(self, cond, stmts):
    self.cond = cond
    self.stmts = stmts 

  def exe(self, scope):
    _exe_stmts(self.stmts, scope)
    while self.cond.exe(scope):
      _exe_stmts(self.stmts, scope)

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
    field = self.field
    if field is not None and isinstance(field, Literal):
      field = field.exe(scope)
    if scope.exists(self.var):
      scope.set_var(self.var, self.val, field)
    else:
      #TODO no such variable error
      # (we assign it anyway)
      scope.set_var(self.var, self.val, field)

class Var(Statement):
  def __init__(self, key, field=None):
    self.key = key
    self.field = field

  def __str__(self):
    return 'Var({0})'.format(str(self.key))

  def exe(self, scope):
    curr_val = scope.get_var(self.key)
    field = self.field if not isinstance(self.field, Literal) else self.field.exe(scope)
    if isinstance(curr_val, Literal):
      curr_val = curr_val.exe(scope)
    if field is not None:
      curr_val = curr_val[field]
      return curr_val.exe(scope) if isinstance(curr_val, Literal) else curr_val
    else:
      return curr_val 

class Literal(Statement):
  def __init__(self, val):
    self.val = val
  
  def __str__(self):
    return 'Literal({0})'.format(str(self.val))

  def exe(self, scope):
    return self.val

class Op(Statement):
  def __init__(self, func, *kwargs):
    self.func = func
    self.kwargs = kwargs

  def __str__(self):
    return 'Op({0} ? {1})'.format(str(self.kwargs[0]), str(self.kwargs[1]))

  def exe(self, scope):
    return self.func(scope, *self.kwargs)

def render_vars(func):
  def render(scope, *kwargs):
    new_kwargs = []
    for x in kwargs:
      while isinstance(x, Statement):
        x = x.exe(scope)
      new_kwargs.append(x)
    return func(scope, *new_kwargs )
  return render

@render_vars
def Print(scope, *kwargs):
  out = ''.join('\n' if x == '<br />' else x for x in kwargs)
  print(out, end='')

@render_vars
def And(scope, lval, rval):
  return lval and rval

@render_vars
def Or(scope, lval, rval):
  return lval or rval

def Not(scope, val):
  if isinstance(val, Var):
    val = val.exe(scope)
  return not val

@render_vars
def GTE(scope, lval, rval):
  return lval >= rval

@render_vars
def LTE(scope, lval, rval):
  return lval <= rval

@render_vars
def GT(scope, lval, rval):
  return lval > rval

@render_vars
def LT(scope, lval, rval):
  return lval < rval

@render_vars
def EQ(scope, lval, rval):
  return lval == rval

@render_vars
def NE(scope, lval, rval):
  return lval != rval

@render_vars
def Add(scope, lval, rval):
  #TODO type check?
  return lval + rval

@render_vars
def Sub(scope, lval, rval):
  #TODO type check?
  return lval - rval

@render_vars
def Mult(scope, lval, rval):
  #TODO type check?
  return lval * rval

@render_vars
def Div(scope, lval, rval):
  #TODO type check?
  return lval / rval
