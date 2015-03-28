class Scope:
  def __init__(self, parent=None, **kwargs):
    self.parent = parent
    self.scope = {}.update(kwargs)
  
  def update(self, scope):
    self.scope.update(scope.scope)
  
  def decl(self, decl_expr):
    self.scope[decl_expr.var] = None

  def init(self, init_expr):
    self.scope[init_expr.var] = init_expr.val

class Node:
  def __init__(self, scope=None, before=None, after=None):
    self.scope = Scope().update(scope)
    self.before = before
    self.after = after
    self.exprs = []

class Expr:
  pass

class Decl(Expr):
  def __init__(self, var):
    self.var = var

class Init(Expr):
  def __init__(self, var, val):
    self.var = var
    self.val = val
    

