import copy
import sys

from lexer import MiniScriptLexer
from lib import yacc

f_debug = 0
tokens = MiniScriptLexer.tokens

curr_arr = []
curr_obj = {}

# grammar here
def p_script(p):
  'script : START NEWLINE stmts END NEWLINE'
  pass

def p_stmts(p):
  '''stmts : empty
           | stmts meta_stmt NEWLINE
           | stmts meta_stmt ';' NEWLINE
           | stmts NEWLINE
  '''
  pass

def p_meta_stmt(p):
  '''meta_stmt : stmt
               | meta_stmt ';' stmt
  '''
  pass

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
  pass

def p_while_do(p):
  '''while_do :  WHILE '(' bool_expr ')' '{' NEWLINE stmts NEWLINE '}'
  '''
  #TODO while do
  pass

def p_do_while(p):
  '''do_while : DO '{' NEWLINE stmts NEWLINE '}' NEWLINE WHILE '(' bool_expr ')'
  '''
  #TODO do while
  pass

def p_if_block(p):
  '''if_block : I_COND '(' bool_expr ')' '{' NEWLINE stmts NEWLINE '}'
  '''
  #TODO if
  pass

def p_if_else(p):
  '''if_else : if_block E_COND I_COND '(' bool_expr ')' '{' NEWLINE stmts NEWLINE '}'
             | if_else E_COND I_COND '(' bool_expr ')' '{' NEWLINE stmts NEWLINE '}'
  '''
  #TODO elseifs
  pass

def p_else(p):
  '''else : if_block E_COND '{' NEWLINE stmts NEWLINE '}'
          | if_else E_COND '{' NEWLINE stmts NEWLINE '}'
  '''
  #TODO elses
  pass


def p_print(p):
  '''print : WRITE '(' args ')'
  '''
  pass

def p_args(p):
  '''args : empty
          | args ',' expr
          | expr
  '''
  pass

def p_decl(p):
  '''decl : VAR ID'''
  #TODO add var to sym table
  pass

def p_init(p):
  '''init : VAR ID '=' expr'''
  #TODO add var and val to sym table
  pass

def p_assign(p):
  '''assign : ID '=' expr
            | ID '.' ID '=' expr
            | ID '[' expr ']' '=' expr
  '''
  if p[2] == '=':
    #TODO var assign
    pass
  if p[2] == '.':
    #TODO obj assign
    pass
  if p[2] == '[':
    #TODO arr assign
    pass
  pass

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
    p[0] = []
  else:
    p[0] = copy.deepcopy(p[3]) 
    curr_arr = []

def p_arr_vals(p):
  '''arr_vals : expr maybe_newline
              | arr_vals ',' maybe_newline expr maybe_newline
  '''
  if p[2] != ',':
    p[0] = [p[1]]
  else:
    curr_arr.append(p[4])
    p[0] = curr_arr

def p_obj_expr(p):
  '''obj_expr : '{' '}'         
              | '{' maybe_newline fields '}'
  '''
  if p[1] == '{' and p[2] == '}':
    p[0] = {} 
  else:
    p[0] = copy.deepcopy(p[3])
    curr_obj = {}

def p_fields(p):
  '''fields : ID ':' expr maybe_newline
            | fields ',' maybe_newline ID ':' expr maybe_newline
  '''
  if p[2] != ',':
    p[0] = { p[1] : p[3] }
  else:
    curr_obj.update({ p[4] : p[6] })
    p[0] = curr_obj

def p_bool_expr(p):
  '''bool_expr : rel_expr
               | bool_expr AND rel_expr
               | bool_expr OR rel_expr
               | NOT rel_expr
  '''
  if len(p) > 2 and p[2] in '&&||!':
    #TODO bool ops 
    pass
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
    #TODO rel ops
    pass
  else:
    p[0] = p[1]

def p_add_expr(p):
  '''add_expr : mult_expr
              | add_expr '+' mult_expr
              | add_expr '-' mult_expr
  '''
  if len(p) > 2 and p[2] in '+-':
    #TODO add ops
    pass
  else:
    p[0] = p[1]

def p_mult_expr(p):
  '''mult_expr : operand
               | mult_expr '*' operand
               | mult_expr '/' operand
  '''
  if len(p) > 2 and p[2] in '*/':
    #TODO mult ops
    pass
  else:
    p[0] = p[1]

def p_operand(p):
  '''operand : ID
             | INT
             | STRING_LITERAL
             | TRUE
             | FALSE
             | ID '.' ID
             | ID '[' bool_expr ']'
             | '(' bool_expr ')'
  '''
  #TODO ops
  pass

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
'''
import logging
logging.basicConfig(
    level = logging.DEBUG,
    filename = "parselog.txt",
    filemode = "w",
    format = "%(filename)10s:%(lineno)4d:%(message)s"
    )
log = logging.getLogger()
'''
yacc.yacc(debug=f_debug)

# Main
#print(sys.argv)
if len(sys.argv) >= 2:
  src_lines = ''
  with open(sys.argv[1], 'r') as src:
   src_lines = ''.join(src.readlines()) 
  #print(src_lines)
  yacc.parse(src_lines) #, debug=log)

else:
  print('usage: ./parser [filename]')
