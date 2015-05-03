from __future__ import print_function
import copy
import logging
import sys

from lexer import MiniScriptLexer
from lib import yacc
from my_ast import *

def only_lits(stmt):
  if isinstance(stmt, Literal):
    return True
  else:
    #Should only be an op
    ret = []
    for k in stmt.kwargs:
      ret.append(only_lits(k))
    return False not in ret

class MiniScriptParser:
  def __init__(self, debug=0):
    self.debug = debug
    self.root_scope = Scope()
    self.root = Block()
    self.curr_arr = []
    self.curr_obj = {}
    self.curr_stmts =[]
    self.curr_scope = self.root_scope
    self.stack = []
    self.funcs = {}
    self.tokens = MiniScriptLexer.tokens
    self.lexer = MiniScriptLexer()
    self.lexer.build()
    logging.basicConfig(
        level = logging.DEBUG,
        filename = "parselog.txt",
        filemode = "w",
        format = "%(filename)10s:%(lineno)4d:%(message)s"
        )
    self.log = logging.getLogger()
    self.parser = yacc.yacc(module=self, debug=self.debug)

  def parse(self, code):
    if code:
      if self.debug:
        self.parser.parse(code, lexer=self.lexer.lexer, debug=self.log)
      else:
        self.parser.parse(code, lexer=self.lexer.lexer)
      return (self.root, self.root_scope)
    else:
      return None
    
  def p_script(self, p):
    'script : newlines START NEWLINE stmts END newlines'
    #dont do normal stack handling because script only happens once
    self.root.stmts = self.curr_stmts

  def p_newlines(sefl, p):
    '''newlines : empty
                | newlines NEWLINE
    '''
    pass
  def p_stmts(self, p):
    '''stmts : empty
             | stmts meta_stmt NEWLINE
             | stmts meta_stmt ';' NEWLINE
             | stmts do_while ';' NEWLINE
             | stmts do_while NEWLINE
             | stmts NEWLINE
    '''
    if len(p) > 3:
      self.curr_stmts.extend(p[2])
      p[0] = self.curr_stmts 
    elif len(p) > 2:
      p[0] = self.curr_stmts
    else:
      p[0] = self.curr_stmts

  def p_meta_stmt(self, p):
    '''meta_stmt : stmt
                 | meta_stmt ';' stmt
    '''
    if len(p) > 2:
      vals = []
      vals.extend(p[1])
      vals.append(p[3])
      p[0] = vals 
    else:
      p[0] = [p[1]]

  def p_stmt(self, p):
    '''stmt : decl
            | init
            | assign
            | print
            | func_call
            | assert 
            | returny
            | func
            | if_block
            | if_else
            | else
            | while_do
            | brake
            | continue
    '''
    p[0] = p[1]

  def p_push_stmts(self, p):
    'push_stmts : empty'
    if self.debug:
      print("Pushing to stack")
    self.stack.append(self.curr_stmts)
    self.curr_stmts = []

  def pop_stmts(self):
    if self.debug:
      print("Popping from stack")
    new_stmts = self.stack.pop()
    self.curr_stmts = new_stmts if new_stmts is not None else []

  def p_brake(self, p):
    'brake : BREAK'
    p[0] = Break()

  def p_continue(self, p):
    'continue : CONT'
    p[0] = Continue()
  
  def p_while_do(self, p):
    '''while_do :  WHILE '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
    '''
    p[0] = While(p[3], self.curr_stmts, p.lineno(1))
    self.pop_stmts()

  def p_doish(self, p):
    'doish : '
    p[0] = DoWhile(None, self.curr_stmts, 0)
    self.pop_stmts()

  def p_do_while(self, p):
    '''do_while : DO '{' NEWLINE push_stmts stmts '}' NEWLINE WHILE '(' doish bool_expr ')'
    '''
    p[10].lineno = p.lineno(8)
    p[10].cond = Condition(p[11])
    p[0] = [p[10]]

  def p_if_block(self, p):
    '''if_block : I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
    '''
    p[0] = If(p[3], self.curr_stmts, p.lineno(1))
    self.pop_stmts()

  def p_if_else(self, p):
    '''if_else : if_block E_COND I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
               | if_else E_COND I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
    '''
    p[1].soit = If(p[5], self.curr_stmts, p.lineno(3))
    p[0] = p[1]
    self.pop_stmts()

  def p_else(self, p):
    '''else : if_block E_COND '{' NEWLINE push_stmts stmts '}'
            | if_else E_COND '{' NEWLINE push_stmts stmts '}'
    '''
    p[1].soit = Block(self.curr_stmts)
    p[0] = p[1]
    self.pop_stmts()

  def p_assert(self, p):
    ''' assert : ASS '(' bool_expr ')' '''
    p[0] = Assert(p[3], p.lineno(1))


  def p_print(self, p):
    '''print : WRITE '(' push_stmts args ')'
    '''
    tmp_args = self.curr_stmts
    p[0] = Op(Print,p.lineno(1), *tmp_args)
    if self.debug:
      print(p[0])
    self.pop_stmts()

  def p_returny(self, p):
    ''' returny : RET expr'''
    #TODO exit if not in function?
    p[0] = RetVal(p[2]) 

  def p_func_call(self, p):
    '''func_call : ID '(' push_stmts args ')'
    '''
    tmp_args = self.curr_stmts
    #TODO func doesn't exist
    p[0] = FunctionCall(p[1], tmp_args, self.root_scope, self.funcs, p.lineno(1))
    self.pop_stmts()

  def p_func(self, p):
    '''func : FUNCTION ID '(' push_stmts dumb_args ')' '{' NEWLINE push_stmts stmts '}' 
    '''
    tmp_stmts = self.curr_stmts
    self.pop_stmts()
    tmp_args = self.curr_stmts
    my_func = Function(p[2], tmp_args, tmp_stmts, p.lineno(1))
    self.funcs[p[2]] = my_func 
    p[0] = my_func
    self.pop_stmts()

  def p_dumb_args(self, p):
    '''dumb_args : empty
            | dumb_args ',' ID 
            | ID 
    '''
    if len(p) > 2:
      self.curr_stmts.append(p[3])
      p[0] = self.curr_stmts
    elif p[1]:
      self.curr_stmts.append(p[1])
      p[0] = self.curr_stmts
    else:
      p[0] = self.curr_stmts
    
  def p_args(self, p):
    '''args : empty
            | args ',' expr
            | expr
            | args ',' func_call 
            | func_call 
    '''
    if len(p) > 2:
      self.curr_stmts.append(p[3])
      p[0] = self.curr_stmts
    elif p[1]:
      self.curr_stmts.append(p[1])
      p[0] = self.curr_stmts
    else:
      p[0] = self.curr_stmts

  def p_decl(self, p):
    '''decl : VAR ID'''
    p[0] = Decl(p[2], p.lineno(2))

  def p_init(self, p):
    '''init : VAR ID '=' expr'''
    p[0] = Init(p[2], p[4], p.lineno(2))
    if self.debug:
      print('Init: {0} = {1}'.format(p[2], p[4]))

  def p_assign(self, p):
    '''assign : ID '=' bool_expr 
              | ID '.' ID '=' bool_expr
              | ID '[' expr ']' '=' bool_expr
    '''
    if p[2] == '=':
      p[0] = Assign(p[1], p[3], p.lineno(1))
    if p[2] == '.':
      p[0] = Assign(p[1], p[5], p.lineno(1), field=p[3])
    if p[2] == '[':
      p[0] = Assign(p[1], p[6], p.lineno(1), field=p[3])
    if self.debug:
      pre = p[1]
      post = p[3]
      if p[2] == '.':
        pre = '{0}.{1}'.format(p[1], p[3])
        post = p[5] 
      if p[2] == '[':
        pre = '{0}[{1}]'.format(p[1], p[3])
        post = p[6]
      print('Assign: {0} = {1}'.format(pre,post))

  def p_expr(self, p):
    '''expr : bool_expr
            | arr_expr
            | obj_expr
    '''
    p[0] = p[1]

  def p_arr_expr(self, p):
    '''arr_expr : '[' ']'
                | '[' maybe_newline arr_vals ']'
    '''
    if p[1] == '[' and p[2] == ']':
      p[0] = {-1:-1} 
    else:
      arr = copy.deepcopy(p[3]) 
      arr = dict([(i,x) for i,x in enumerate(arr)])
      arr_w_lit_eval = {}
      for x in arr.keys():
        if only_lits(arr[x]):
          arr_w_lit_eval[x] = arr[x].exe(None)
      arr_w_lit_eval[-1] = -1
      p[0] = arr_w_lit_eval
      self.curr_arr = []

  def p_arr_vals(self, p):
    '''arr_vals : expr maybe_newline
                | arr_vals ',' maybe_newline expr maybe_newline
    '''
    if p[2] != ',':
      self.curr_arr.append(p[1])
      p[0] = self.curr_arr
    else:
      self.curr_arr.append(p[4])
      p[0] = self.curr_arr

  def p_obj_expr(self, p):
    '''obj_expr : '{' '}'         
                | '{' maybe_newline fields '}'
    '''
    if p[1] == '{' and p[2] == '}':
      p[0] = {} 
    else:
      dic = copy.deepcopy(p[3])
      dic_w_lit_eval = {}
      for x in dic.keys():
        if only_lits(dic[x]):
          dic_w_lit_eval[x] = dic[x].exe(None)
      p[0] = dic     
      self.curr_obj = {}

  def p_fields(self, p):
    '''fields : ID ':' expr maybe_newline
              | fields ',' maybe_newline ID ':' expr maybe_newline
    '''
    if p[2] != ',':
      self.curr_obj.update({ p[1] : p[3]})
      p[0] = self.curr_obj
    else:
      self.curr_obj.update({ p[4] : p[6]})
      p[0] = self.curr_obj

  def p_bool_expr(self, p):
    '''bool_expr : rel_expr
                 | bool_expr AND rel_expr
                 | bool_expr OR rel_expr
    '''
    if len(p) > 3 and p[2] in '&&||':
      func = And if p[2] == '&&' else Or
      lineno = p.lineno(1)
      if isinstance(p[1], Statement):
        lineno = p[1].lineno
      if isinstance(p[2], Statement):
        lineno = p[2].lineno
      p[0] = Op(func, lineno, p[1], p[3])
      if self.debug:
        print('Op: {0} {1} {2}'.format(p[1], p[2], p[3]))
    else:
      p[0] = p[1]

  def p_rel_expr(self, p):
    '''rel_expr : add_expr
                | rel_expr EQ add_expr
                | rel_expr NE add_expr
                | rel_expr GTE add_expr
                | rel_expr LTE add_expr
                | rel_expr GT add_expr
                | rel_expr LT add_expr
    '''
    if len(p) > 2 and p[2] in '==!=>=<=':
      func = EQ if p[2] == '==' else NE if p[2] == '!=' else \
          GTE if p[2] == '>=' else LTE if p[2] == '<=' else \
          GT if p[2] == '>' else LT
      lineno = p.lineno(1)
      if isinstance(p[1], Statement):
        lineno = p[1].lineno
      if isinstance(p[2], Statement):
        lineno = p[2].lineno
      p[0] = Op(func, lineno, p[1], p[3])
      if self.debug:
        print('Op: {0} {1} {2}'.format(p[1], p[2], p[3]))
    else:
      p[0] = p[1]

  def p_add_expr(self, p):
    '''add_expr : mult_expr
                | add_expr '+' mult_expr
                | add_expr '-' mult_expr
    '''
    if len(p) > 2 and p[2] in '+-':
      func = Add if p[2] == '+' else Sub
      lineno = p.lineno(1)
      if isinstance(p[1], Statement):
        lineno = p[1].lineno
      if isinstance(p[2], Statement):
        lineno = p[2].lineno
      p[0] = Op(func, lineno, p[1], p[3])
    else:
      p[0] = p[1]

  def p_mult_expr(self, p):
    '''mult_expr : operand
                 | mult_expr '*' operand
                 | mult_expr '/' operand
    '''
    if len(p) > 2 and p[2] in '*/':
      func = Mult if p[2] == '*' else Div
      lineno = p.lineno(1)
      if isinstance(p[1], Statement):
        lineno = p[1].lineno
      if isinstance(p[2], Statement):
        lineno = p[2].lineno
      p[0] = Op(func, lineno, p[1], p[3])
    else:
      p[0] = p[1]

  def p_operand(self, p):
    '''operand : constant 
               | var_access
               | func_call
               | '(' bool_expr ')'
               | NOT '(' bool_expr ')'
               | NOT var_access
    '''
    if p[1] == '(':
      p[0] = p[2]
    elif p[1] == '!':
      lineno = p.lineno(1)
      if p[2] == '(':
        if isinstance(p[3], Statement):
          lineno = p[3].lineno
        p[0] = Op(Not, lineno, p[3])
        if self.debug:
          print('Op: !{0}'.format(p[3]))
      else:
        if isinstance(p[2], Statement):
          lineno = p[2].lineno
        p[0] = Op(Not, lineno, p[2])
        if self.debug:
          print('Op: !{0}'.format(p[2]))
    else:
      p[0] = p[1]

  def p_var_access(self, p):
    '''var_access : ID
                  | ID '.' ID
                  | ID '[' bool_expr ']'
    '''
    if len(p)>4:
      p[0] = Var(p[1], p.lineno(1), p[3])
    elif len(p)>2:
      p[0] = Var(p[1], p.lineno(1), p[3])
    else:
      p[0] = Var(p[1], p.lineno(1))

  def p_constant(self, p):
    '''constant : INT
                | STRING_LITERAL
                | TRUE
                | FALSE
    '''
    p[0] = Literal(p[1], p.lineno(1))

  def p_maybe_newline(self, p):
    '''maybe_newline : empty
                     | maybe_newline NEWLINE
    '''
    pass

  def p_empty(self, p):
    'empty :'
    pass

  def p_error(self, p):
    if self.debug:
      print('ERROR: {0}'.format(p), file=sys.stderr)
    else:
      print('syntax error', file=sys.stderr)
