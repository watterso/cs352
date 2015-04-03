import copy
import sys

from lexer import MiniScriptLexer
from lib import yacc
from my_ast import *

debug = 1
f_debug = debug

tokens = MiniScriptLexer.tokens

curr_arr = []
curr_obj = {}
root_scope = Scope()
root = Block()
curr_stmts =[]
stack = []

def _render_literal(scope, lit, real=False):
  if real:
    return lit.exe(scope) if isinstance(lit, Statement) else lit
  else:
    return lit

# grammar here
def p_script(p):
  'script : START NEWLINE stmts END NEWLINE'
  #dont do normal stack handling because script only happens once
  root.stmts = curr_stmts

def p_stmts(p):
  '''stmts : empty
           | stmts meta_stmt NEWLINE
           | stmts meta_stmt ';' NEWLINE
           | stmts NEWLINE
  '''
  if len(p) > 3:
    curr_stmts.extend(p[2])
    p[0] = curr_stmts 
  elif len(p) > 2:
    p[0] = curr_stmts
  else:
    p[0] = curr_stmts

def p_meta_stmt(p):
  '''meta_stmt : stmt
               | meta_stmt ';' stmt
  '''
  if len(p) > 2:
    p[0] = [p[1], p[3]]
  else:
    p[0] = [p[1]]

def p_stmt(p):
  '''stmt : decl
          | init
          | assign
          | print
          | if_block
          | if_else
          | else
          | do_while
          | while_do
  '''
  p[0] = p[1]

def p_push_stmts(p):
  'push_stmts : empty'
  if debug:
    print("Pushing to stack")
  global curr_stmts
  stack.append(copy.deepcopy(curr_stmts))
  curr_stmts = []

def pop_stmts():
  if debug:
    print("Popping from stack")
  global curr_stmts
  new_stmts = stack.pop()
  curr_stmts = new_stmts if new_stmts is not None else []

def p_while_do(p):
  '''while_do :  WHILE '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
  '''
  p[0] = While(p[3], curr_stmts)
  pop_stmts()

def p_doish(p):
  'doish : '
  p[0] = DoWhile(None, curr_stmts)
  pop_stmts()

def p_do_while(p):
  '''do_while : DO '{' NEWLINE push_stmts stmts '}' NEWLINE WHILE '(' doish bool_expr ')'
  '''
  p[10].cond = p[11]
  p[0] = p[10]

def p_if_block(p):
  '''if_block : I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
  '''
  p[0] = If(p[3], curr_stmts)
  pop_stmts()

def p_if_else(p):
  '''if_else : if_block E_COND I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
             | if_else E_COND I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
  '''
  p[1].soit = If(p[5], curr_stmts)
  p[0] = p[1]
  pop_stmts()

def p_else(p):
  '''else : if_block E_COND '{' NEWLINE push_stmts stmts '}'
          | if_else E_COND '{' NEWLINE push_stmts stmts '}'
  '''
  p[1].soit = Block(curr_stmts)
  p[0] = p[1]
  pop_stmts()


def p_print(p):
  '''print : WRITE '(' push_stmts args ')'
  '''
  tmp_args = curr_stmts
  p[0] = Op(Print, *tmp_args)
  pop_stmts()
  
def p_args(p):
  '''args : empty
          | args ',' expr
          | expr
  '''
  if len(p) > 2:
    curr_stmts.append(p[3])
    p[0] = curr_stmts
  elif p[1]:
    curr_stmts.append(p[1])
    p[0] = curr_stmts
  else:
    p[0] = curr_stmts

def p_decl(p):
  '''decl : VAR ID'''
  p[0] = Decl(p[2])

def p_init(p):
  '''init : VAR ID '=' expr'''
  p[0] = Init(p[2], _render_literal(root_scope, p[4]))
  if debug:
    print('Init: {0} = {1}'.format(p[2], _render_literal(root_scope, p[4], True)))

def p_assign(p):
  '''assign : ID '=' expr
            | ID '.' ID '=' expr
            | ID '[' expr ']' '=' expr
  '''
  if p[2] == '=':
    p[0] = Assign(p[1], _render_literal(root_scope, p[3]))
  if p[2] == '.':
    p[0] = Assign(p[1], _render_literal(root_scope, p[5]), field=_render_literal(root_scope, p[3]))
  if p[2] == '[':
    p[0] = Assign(p[1], _render_literal(root_scope, p[6]), field=_render_literal(root_scope, p[3]))
  if debug:
    pre = p[1]
    post = p[3]
    if p[2] == '.':
      pre = '{0}.{1}'.format(p[1], _render_literal(root_scope, p[3], True))
      post = _render_literal(root_scope, p[5], True)
    if p[2] == '[':
      pre = '{0}[{1}]'.format(p[1], _render_literal(root_scope, p[3], True))
      post = _render_literal(root_scope, p[6], True)
    print('Assign: {0} = {1}'.format(pre,post))

def p_expr(p):
  '''expr : bool_expr
          | arr_expr
          | obj_expr
  '''
  p[0] = p[1]

def p_arr_expr(p):
  '''arr_expr : '[' ']'
              | '[' maybe_newline arr_vals ']'
  '''
  if p[1] == '[' and p[2] == ']':
    p[0] = {-1:-1} 
  else:
    arr = copy.deepcopy(p[3]) 
    arr = dict([(i,x) for i,x in enumerate(arr)])
    arr[-1] = -1
    p[0] = arr
    curr_arr = []

def p_arr_vals(p):
  '''arr_vals : expr maybe_newline
              | arr_vals ',' maybe_newline expr maybe_newline
  '''
  if p[2] != ',':
    curr_arr.append(_render_literal(root_scope, p[1]))
    p[0] = curr_arr
  else:
    curr_arr.append(_render_literal(root_scope, p[4]))
    p[0] = curr_arr

def p_obj_expr(p):
  '''obj_expr : '{' '}'         
              | '{' maybe_newline fields '}'
  '''
  if p[1] == '{' and p[2] == '}':
    p[0] = {} 
  else:
    curr_obj = {}
    p[0] = copy.deepcopy(p[3])
    curr_obj = {}

def p_fields(p):
  '''fields : ID ':' expr maybe_newline
            | fields ',' maybe_newline ID ':' expr maybe_newline
  '''
  if p[2] != ',':
    curr_obj.update({ p[1] : _render_literal(root_scope, p[3])})
    p[0] = curr_obj
  else:
    curr_obj.update({ p[4] : _render_literal(root_scope, p[6])})
    p[0] = curr_obj

def p_bool_expr(p):
  '''bool_expr : rel_expr
               | bool_expr AND rel_expr
               | bool_expr OR rel_expr
               | NOT rel_expr
  '''
  if len(p) > 3 and p[2] in '&&||':
    func = And if p[2] == '&&' else Or
    p[0] = Op(func, p[1], p[3])
    if debug:
      print('Op: {0} {1} {2}'.format(p[1], p[2], p[3]))
  elif p[1] == '!':
    p[0] = Op(Not, p[2])
    if debug:
      print('Op: !{0}'.format(p[2]))
  else:
    p[0] = p[1]

def p_rel_expr(p):
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
    p[0] = Op(func, p[1], p[3])
    if debug:
      print('Op: {0} {1} {2}'.format(p[1], p[2], p[3]))
  else:
    p[0] = p[1]

def p_add_expr(p):
  '''add_expr : mult_expr
              | add_expr '+' mult_expr
              | add_expr '-' mult_expr
  '''
  if len(p) > 2 and p[2] in '+-':
    func = Add if p[2] == '+' else Sub
    p[0] = Op(func, p[1], p[3])
  else:
    p[0] = p[1]

def p_mult_expr(p):
  '''mult_expr : operand
               | mult_expr '*' operand
               | mult_expr '/' operand
  '''
  if len(p) > 2 and p[2] in '*/':
    func = Mult if p[2] == '*' else Div
    p[0] = Op(func, p[1], p[3])
  else:
    p[0] = p[1]

def p_operand(p):
  '''operand : constant 
             | var_access
             | '(' bool_expr ')'
  '''
  if len(p) > 2:
    p[0] = p[2]
  else:
    p[0] = p[1]

def p_var_access(p):
  '''var_access : ID
                | ID '.' ID
                | ID '[' bool_expr ']'
  '''
  if len(p)>4:
    p[0] = Var(p[1], p[3])
  elif len(p)>2:
    p[0] = Var(p[1], p[3])
  else:
    p[0] = Var(p[1])

def p_constant(p):
  '''constant : INT
              | STRING_LITERAL
              | TRUE
              | FALSE
  '''
  p[0] = Literal(p[1])

def p_maybe_newline(p):
  '''maybe_newline : empty
                   | maybe_newline NEWLINE
  '''
  pass

def p_empty(p):
  'empty :'
  pass

def p_error(p):
  print('ERROR: {0}'.format(p))

m = MiniScriptLexer()
m.build()

import logging
logging.basicConfig(
    level = logging.DEBUG,
    filename = "parselog.txt",
    filemode = "w",
    format = "%(filename)10s:%(lineno)4d:%(message)s"
    )
log = logging.getLogger()
yacc.yacc(debug=f_debug)

# Main
#print(sys.argv)
if len(sys.argv) >= 2:
  src_lines = ''
  with open(sys.argv[1], 'r') as src:
   src_lines = ''.join(src.readlines()) 
  #print(src_lines)
  if debug:
    yacc.parse(src_lines, debug=log)
  else:
    yacc.parse(src_lines)
  root.exe(root_scope)
  #print(root_scope)

else:
  print('usage: ./parser [filename]')
