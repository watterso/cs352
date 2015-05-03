from __future__ import print_function
import json
import sys

ERR_PREFIX = 'Line {0}, '
COND_UNKNOWN = 'condition unknown'
VAR_UNDECL = '{0} undeclared'
TYPE_VIOL = 'type violation'
VALUE_ERR = '{0} has no value'
err_str = None
err_printed = False

reported = []

def spec_err(err):
  global err_printed
  global err_str
  if err_str is None:
    err_printed = False
    err_str = err

def num_print_err(stmt):
  global err_printed
  global err_str
  global reported
  lineno = stmt.lineno
  if err_str is not None and not err_printed and \
      stmt not in reported:
    pre = ERR_PREFIX.format(lineno)
    final = '{0}{1}'.format(pre, err_str)
    print(final, file=sys.stderr)
    err_printed = True
    reported.append(stmt)

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
      elif isinstance(st, RetVal):
        raise st
        #return st.exe(scope)
      else:
        ret = st.exe(scope)
        if err_printed:
          err_printed = False
          err_str = None
        #if ret is not None:
        #  return ret

class Scope:
  def __init__(self, parent=None, **kwargs):
    self.parent = parent
    self.scope = {}
    self.written_dict = {}
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
    for key, val in a_dict.iteritems():
      self.set_var(key, val)

  def written(self, writ, var, val, field=None, recurse=True):
    if recurse:
      res = self._find(var)
      if res:
        res[0].written(writ, var, val, field, False)
      else:
        self.written_dict[pretty_var(var, val, field)] = writ
    else:
        self.written_dict[pretty_var(var, val, field)] = writ

  def is_written(self, var, recurse=True):
    if recurse:
      res = self._find(var)
      if res:
        return res[0].is_written(var, False)
      else:
        return False
    else:
      return var in self.written_dict and self.written_dict[var]      

  def set_var(self, var, val=None, field=None, recurse=True):
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
    try:
      _exe_stmts(self.stmts, scope)
    except RetVal as r:
      raise 

class ConditionUnknown(Exception):
  pass

class Condition(Statement):
  def __init__(self, cond):
    self.cond = cond

  def __str__(self):
    return 'Cond({0})'.format(self.cond)
  
  def exe(self, scope):
    cond = self.cond.exe(scope)
    if cond is None:
      spec_err(COND_UNKNOWN)
      raise ConditionUnknown()
    else:
      cond = render_val(scope, cond)
      return cond

class RetVal(Statement, Exception):
  def __init__(self, expr):
    self.expr = expr

  def __str__(self):
    return 'return {0}'.format(self.expr)

  def exe(self, scope):
    ret = self.expr.exe(scope)
    return ret

class FunctionCall(Statement):
  def __init__(self, name, args, parent_scope, func_list, lineno):
    self.name = name
    self.args = args
    self.p_scope = parent_scope
    self.lineno = lineno
    self.funcs = func_list

  def __str__(self):
    return '{0}({1})'.format(self.name, ','.join(map(my_str, self.args)))

  def exe(self, scope):
    m_scope = Scope(self.p_scope)
    func = self.funcs[self.name]
    rendered_args = [render_val(scope, x) for x in self.args]
    return func.run(m_scope, rendered_args)

class Function(Statement):
  def __init__(self, name, args, stmts, lineno):
    self.name = name
    self.args = args
    self.stmts = stmts
    self.lineno = lineno

  def __str__(self):
    return '{0}({1})'.format(self.name, ','.join(self.args))

  def run(self, scope, args):
    arguments = dict(zip(self.args, [render_val(scope,x) for x in args]))
    scope.set_vars(arguments)
    try:
      _exe_stmts(self.stmts, scope)
    except RetVal as r:
      return r.exe(scope)

class If(Statement):
  def __init__(self, cond, stmts, lineno,soit=None):
    self.cond = Condition(cond)
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
      num_print_err(self)
    except RetVal as r:
      raise 

class While(Statement):
  def __init__(self, cond, stmts, lineno):
    self.cond = Condition(cond)
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
        except RetVal as r:
          return r
    except ConditionUnknown:
      num_print_err(self)
      pass
      
class DoWhile(Statement):
  def __init__(self, cond, stmts, lineno):
    self.cond = Condition(cond)
    self.stmts = stmts 
    self.lineno = lineno

  def __str__(self):
    return 'DoWhile<{0}>'.format(self.cond)

  def exe(self, scope):
    do_while = True
    try:
      _exe_stmts(self.stmts, scope)
    except Break:
      do_while = False
    except Continue:
      pass
    except RetVal as r:
      return r
    if do_while:
      try:
        while self.cond.exe(scope):
          try:
            _exe_stmts(self.stmts, scope)
          except Break:
            break
          except Continue:
            continue
          except RetVal as r:
            return r
      except ConditionUnknown:
        num_print_err(self)

class Decl(Statement):
  def __init__(self, var, lineno):
    self.var = var
    self.lineno = lineno

  def __str__(self):
    return 'Decl<{0}>'.format(self.var)

  def exe(self, scope):
    scope.set_var(self.var, None, recurse=False)
    #this scope, unwritten
    scope.written(False, self.var, None, recurse=False)

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
    #this scope, written
    scope.written(True, self.var, r_val, recurse=False)

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
        if field is None:
          # arr or obj getting redefined
          for k in curr_val.keys():
            if k == -1:
              continue
            #all keys unwritten
            scope.written(False, self.var, curr_val, k)

          scope.written(True, self.var, curr_val, field)
          scope.set_var(self.var, val, field)
          if type(val) is dict:
            for k in curr_val.keys():
              if k == -1:
                continue
              #all keys written
              comp = pretty_var(self.var, val, k) 
              scope.written(True, self.var, curr_val, k)

        else:
          f_typ = type(field)
          if f_typ not in [int, str]:
            #Field Type VIOL
            spec_err(TYPE_VIOL)
            num_print_err(self)
          elif f_typ is str and is_array(curr_val):
            #Access array with obj key ERROR
            spec_err(TYPE_VIOL)
            num_print_err(self)
          else:
            #success on dict or array
            scope.written(True, self.var, curr_val, field)
            scope.set_var(self.var, val, field)
      else:
        if field is not None:
          #treating var as dict
          spec_err(TYPE_VIOL)
          num_print_err(self)
        else:
          #success on primitive
          scope.written(True, self.var, val, field)
          scope.set_var(self.var, val, field)
    else:
      # variable not declared error
      # (we assign it anyway)
      spec_err(VAR_UNDECL.format(self.var))
      num_print_err(self)
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
      if not scope.is_written(self.key):      
        spec_err(VALUE_ERR.format(self.key))
        num_print_err(self)
      return None
    else:  
      if self.field is not None:
        if r_field is None:
          #bad field val
          comp = pretty_var(self.key, curr_val, r_field) 
          spec_err(VAR_UNDECL.format(comp))
          num_print_err(self)
          return None
        elif type(curr_val) not in [dict, list]:
          spec_err(TYPE_VIOL)
          num_print_err(self)
        elif type(r_field) is int and not is_array(curr_val) or \
            type(r_field) is str and is_array(curr_val) or \
            type(r_field) not in [int, str]:
          spec_err(TYPE_VIOL)
          num_print_err(self)
        elif r_field not in curr_val:
          #var[field] has no value
          comp = pretty_var(self.key, curr_val, r_field) 
          if not scope.is_written(comp):
            spec_err(VALUE_ERR.format(comp))
            num_print_err(self)
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
    #print('exec\'ing : '+str(self))
    ret = self.func(scope, *self.kwargs)
    if ret is None:
      num_print_err(self)
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

def cripple_print(k):
  if type(k) in [list, dict]:
    spec_err(TYPE_VIOL)
    return None
  else:
    return k

@render_vars
def Print(scope, *kwargs):
  kwargs = map(cripple_print, kwargs)
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
      elif lval is None or rval is None:
        return None
      else:
        #type violation 
        spec_err(TYPE_VIOL)
        return None
    return check 
  return la


#TODO TODO TODO type check And and Or

def And(scope, lval, rval):
  #render_val instead of decorator for short circuit
  return bool(render_val(scope, lval)) and bool(render_val(scope, rval))

def Or(scope, lval, rval):
  return bool(render_val(scope, lval)) or bool(render_val(scope, rval))

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
