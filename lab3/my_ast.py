from __future__ import print_function
import copy
import json
import sys

ERR_PREFIX = 'Line {0}, '
COND_UNKNOWN = 'condition unknown'
VAR_UNDECL = '{0} undeclared'
TYPE_VIOL = 'type violation'
VALUE_ERR = '{0} has no value'
err_str = None
err_printed = False

def spec_err(err):
  global err_printed
  global err_str
  if err_str is None:
    err_printed = False
    err_str = err

def num_print_err(lineno):
  global err_printed
  global err_str
  if err_str is not None and not err_printed:
    pre = ERR_PREFIX.format(lineno)
    final = '{0}{1}'.format(pre, err_str)
    print(final, file=sys.stderr)
    err_printed = True

def my_str(val):
  typ = type(val)
  if val is None:
    return 'undefined'
  elif typ is bool:
    return 'true' if val else 'false'
  else:
    return str(val)

def pretty_var(var, curr_val, field=None):
  if field is not None:
    access = ''
    if is_array(curr_val):
      access = '[{0}]'.format(field)
    else:
      access = '.{0}'.format(field)
    comp = '{0}{1}'.format(var, access)
    return comp
  else:
    return var

def is_array(a_dict):
  #return not False in [type(k) is int for k in a_dict.keys()]
  return -1 in a_dict.keys()

def render_val(scope, val):
  while val is not None and isinstance(val, Statement):
    val = val.exe(scope)
  return val


def _exe_stmts(stmts, scope):
  global err_printed
  global err_str
  for st in stmts:
    if st:
      if isinstance(st, Break):
        raise Break()
      elif isinstance(st, Continue):
        raise Continue()
      else:
        st.exe(scope)
        if err_printed:
          err_printed = False
          err_str = None

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
    return True if self._find(var) is not None else False

  def defined(self, var):
    return self.exists(var) and self._find(var)[1] is not None

  def get_var(self, var):
    res = self._find(var)
    if res is not None:
      return res[1]
    else:
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
  def __repr__(self):
    return str(self)

  def exe(self, scope):
    pass

class Block(Statement):
  def __init__(self, stmts=[]):
    self.stmts = stmts

  def __str__(self):
    return 'Block<{0}>'.format(len(self.stmts))

  def exe(self, scope):
    _exe_stmts(self.stmts, scope)

class ConditionUnknown(Exception):
  pass

class Condition(Statement):
  def __init__(self, cond):
    self.cond = cond

  def __str__(self):
    return str(self.cond)
  
  def exe(self, scope):
    cond = self.cond.exe(scope)
    if cond is None:
      raise ConditionUnknown()
    else:
      return cond

class If(Statement):
  def __init__(self, cond, stmts, lineno,soit=None):
    self.cond = cond
    self.soit = soit
    self.stmts = stmts
    self.lineno = lineno

  def __str__(self):
    return 'If<{0}>'.format(self.cond)

  def exe(self, scope): 
    try:
      if self.cond.exe(scope):
        _exe_stmts(self.stmts, scope)
      elif self.soit is not None:
        self.soit.exe(scope)
    except ConditionUnknown:
      #TODO report condtion unknown
      pass

class While(Statement):
  def __init__(self, cond, stmts, lineno):
    self.cond = cond
    self.stmts = stmts 
    self.lineno = lineno

  def __str__(self):
    return 'While<{0}>'.format(self.cond)

  def exe(self, scope):
    try:
      while self.cond.exe(scope):
        try:
          _exe_stmts(self.stmts, scope)
        except Break:
          break
        except Continue:
          continue
    except ConditionUnknown:
      #TODO report condtion unknown
      pass
      
class DoWhile(Statement):
  def __init__(self, cond, stmts, lineno):
    self.cond = cond
    self.stmts = stmts 
    self.lineno = lineno

  def __str__(self):
    return 'DoWhile<{0}>'.format(self.cond)

  def exe(self, scope):
    _exe_stmts(self.stmts, scope)
    try:
      while self.cond.exe(scope):
        _exe_stmts(self.stmts, scope)
    except ConditionUnknown:
      #TODO report condtion unknown
      pass

class Decl(Statement):
  def __init__(self, var, lineno):
    self.var = var
    self.lineno = lineno

  def __str__(self):
    return 'Decl<{0}>'.format(self.var)

  def exe(self, scope):
    scope.set_var(self.var, None, recurse=False)

class Init(Statement):
  def __init__(self, var, val, lineno):
    self.var = var
    self.val = val
    self.lineno = lineno

  def __str__(self):
    return 'Init<{0},{1}>'.format(self.var, self.val)

  def exe(self, scope):
    r_val = render_val(scope, self.val)
    scope.set_var(self.var, r_val, recurse=False)

class Assign(Statement):
  def __init__(self, var, val, lineno, field=None):
    self.var = var
    self.val = val
    self.field = field
    self.lineno = lineno

  def __str__(self):
    if self.field is None:
      return 'Assign<{0},{1}>'.format(self.var, self.val)
    else:
      return 'Assign<{0}[{1}],{2}>'.format(self.var, self.field, self.val)

  def exe(self, scope):
    field = render_val(scope, self.field)
    val = render_val(scope, self.val)
    curr_val = scope.get_var(self.var)
    curr_val = render_val(scope, curr_val)
    if scope.exists(self.var):
      typ = type(curr_val)
      if typ is dict:
        f_typ = type(field)
        if f_typ not in [int, str]:
          #Field Type VIOL
          spec_err(TYPE_VIOL)
          num_print_err(self.lineno)
        elif f_typ is str and is_array(curr_val):
          #Access array with obj key ERROR
          spec_err(TYPE_VIOL)
          num_print_err(self.lineno)
        else:
          scope.set_var(self.var, val, field)
      else:
        if field is not None:
          #treating var as dict
          spec_err(TYPE_VIOL)
          num_print_err(self.lineno)
        else:
          scope.set_var(self.var, val, field)
    else:
      # variable not declared error
      # (we assign it anyway)
      spec_err(VAR_UNDECL.format(self.var))
      num_print_err(self.lineno)
      scope.set_var(self.var, val, field)

class Var(Statement):
  def __init__(self, key, lineno, field=None):
    self.key = key
    self.field = field
    self.lineno = lineno

  def __str__(self):
    if self.field is None:
      return 'Var<{0}>'.format(my_str(self.key))
    else:
      return 'Var<{0}[{1}]>'.format(self.key, self.field)

  def exe(self, scope):
    curr_val = scope.get_var(self.key)
    curr_val = render_val(scope, curr_val)
    r_field = render_val(scope, self.field)
    if curr_val is None:
      #var has no value
      spec_err(VALUE_ERR.format(self.key))
      num_print_err(self.lineno)
      return None
    else:  
      if self.field is not None:
        if r_field is None:
          #bad field val
          comp = pretty_var(self.key, curr_val, self.field) 
          spec_err(VAR_UNDECL.format(comp))
          num_print_err(self.lineno)
          return None
        elif r_field not in curr_val:
          #var[field] has no value
          comp = pretty_var(self.key, curr_val, self.field) 
          spec_err(VALUE_ERR.format(comp))
          num_print_err(self.lineno)
          return None
        else:
          curr_val = curr_val[r_field]
          return curr_val
      else:
        return curr_val 

class Literal(Statement):
  def __init__(self, val, lineno):
    self.val = val
    self.lineno = lineno
  
  def __str__(self):
    if type(self.val) is str:
      return 'Literal<\'{0}\'>'.format(my_str(self.val))
    else:
      return 'Literal<{0}>'.format(my_str(self.val))

  def exe(self, scope):
    return self.val

class LoopException(Exception):
  pass
class Break(Statement, LoopException):
  pass
class Continue(Statement, LoopException):
  pass

class Op(Statement):
  def __init__(self, func, lineno, *kwargs):
    self.func = func
    self.kwargs = kwargs
    self.lineno = lineno

  def __str__(self):
    kwargs = map(my_str,list(self.kwargs))
    if self.func is not Print:
      if len(kwargs) > 1:
        return 'Op<{0} {2} {1}>'.format(kwargs[0], kwargs[1], self._operator_string())
      else:
        return 'Op<!{0}>'.format(self.kwargs[0])
    else:
      fill = ', '.join(kwargs)
      return 'Op<Print({0})>'.format(fill)

  def _operator_string(self):
    f = self.func
    if f is And:
      return '&&'
    elif f is Or:
      return '||'
    elif f is Add:
      return '+'
    elif f is Sub:
      return '-'
    elif f is Mult:
      return '*'
    elif f is Div:
      return '/'
    else:
      return '?'

  def exe(self, scope):
    ret = self.func(scope, *self.kwargs)
    if ret is None:
      num_print_err(self.lineno)
    else:
      return ret

def render_vars(func):
  def render(scope, *kwargs):
    new_kwargs = []
    for x in kwargs:
      y = x
      while y is not None and isinstance(y, Statement):
        y = y.exe(scope)
      new_kwargs.append(y)
    return func(scope, *new_kwargs)
  return render

@render_vars
def Print(scope, *kwargs):
  arr = ['\n' if my_str(x) == '<br />' else my_str(x) for x in kwargs]
  out = ''.join(arr)
  print(out, end='')


def type_check(args, same=True):
  def la(func):
    def check(scope, lval, rval):
      lt = type(lval)
      rt = type(rval)
      if lt in args and rt in args:
        if not same:
          return func(scope, lval, rval)
        elif rt == lt:
          return func(scope, lval, rval)
        else:
          #type violation
          spec_err(TYPE_VIOL)
          return None
      else:
        #type violation 
        spec_err(TYPE_VIOL)
        return None
    return check 
  return la

@render_vars
@type_check([int,str,bool], False)
def And(scope, lval, rval):
  return lval and rval

@render_vars
@type_check([int,str,bool], False)
def Or(scope, lval, rval):
  return lval or rval

@render_vars
def Not(scope, val):
  return not val

@render_vars
@type_check([int])
def GTE(scope, lval, rval):
  return lval >= rval

@render_vars
@type_check([int])
def LTE(scope, lval, rval):
  return lval <= rval

@render_vars
@type_check([int])
def GT(scope, lval, rval):
  return lval > rval

@render_vars
@type_check([int])
def LT(scope, lval, rval):
  return lval < rval

@render_vars
@type_check([int, str, bool])
def EQ(scope, lval, rval):
  return lval == rval

@render_vars
@type_check([int, str, bool])
def NE(scope, lval, rval):
  return lval != rval

@render_vars
@type_check([int, str])
def Add(scope, lval, rval):
  return lval + rval

@render_vars
@type_check([int])
def Sub(scope, lval, rval):
  return lval - rval

@render_vars
@type_check([int])
def Mult(scope, lval, rval):
  return lval * rval

@render_vars
@type_check([int])
def Div(scope, lval, rval):
  return lval / rval
