import copy
import logging
import sys

from lexer import MiniScriptLexer
from lib import yacc
from my_ast import *

class MiniScriptParser:
  def __init__(self, debug=0):
    self.debug = debug
    self.curr_arr = []
    self.curr_obj = {}
    self.curr_stmts =[]
    self.stack = []
    self.root_scope = Scope()
    self.root = Block()
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
    

  def exe(self):
    self.root.exe(root_scope)

  def print_gen(self):
    _print_stmts(root)

  def _print_stmts(stmt, indent=0):
    print('{0}{1}'.format(' '*2*indent, stmt))
    if hasattr(stmt,'stmts') and stmt.stmts:
      for st in stmt.stmts:
        _print_stmts(st, indent+1)
    if hasattr(stmt,'soit') and stmt.soit:
      print(' '*2*indent+'else:')
      _print_stmts(stmt.soit,indent)

  # grammar here
  def p_script(self, p):
    'script : START NEWLINE stmts END NEWLINE'
    #dont do normal stack handling because script only happens once
    self.root.stmts = self.curr_stmts

  def p_stmts(self, p):
    '''stmts : empty
             | stmts meta_stmt NEWLINE
             | stmts meta_stmt ';' NEWLINE
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
            | if_block
            | if_else
            | else
            | do_while
            | while_do
    '''
    p[0] = p[1]

  def p_push_stmts(self, p):
    'push_stmts : empty'
    if self.debug:
      print("Pushing to stack")
    self.stack.append(copy.deepcopy(self.curr_stmts))
    self.curr_stmts = []

  def pop_stmts(self):
    if self.debug:
      print("Popping from stack")
    new_stmts = self.stack.pop()
    self.curr_stmts = new_stmts if new_stmts is not None else []

  def p_while_do(self, p):
    '''while_do :  WHILE '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
    '''
    p[0] = While(p[3], self.curr_stmts)
    self.pop_stmts()

  def p_doish(self, p):
    'doish : '
    p[0] = DoWhile(None, self.curr_stmts)
    self.pop_stmts()

  def p_do_while(self, p):
    '''do_while : DO '{' NEWLINE push_stmts stmts '}' NEWLINE WHILE '(' doish bool_expr ')'
    '''
    p[10].cond = p[11]
    p[0] = p[10]

  def p_if_block(self, p):
    '''if_block : I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
    '''
    p[0] = If(p[3], self.curr_stmts)
    self.pop_stmts()

  def p_if_else(self, p):
    '''if_else : if_block E_COND I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
               | if_else E_COND I_COND '(' bool_expr ')' '{' NEWLINE push_stmts stmts '}'
    '''
    p[1].soit = If(p[5], self.curr_stmts)
    p[0] = p[1]
    self.pop_stmts()

  def p_else(self, p):
    '''else : if_block E_COND '{' NEWLINE push_stmts stmts '}'
            | if_else E_COND '{' NEWLINE push_stmts stmts '}'
    '''
    p[1].soit = Block(self.curr_stmts)
    p[0] = p[1]
    self.pop_stmts()


  def p_print(self, p):
    '''print : WRITE '(' push_stmts args ')'
    '''
    tmp_args = self.curr_stmts
    p[0] = Op(Print, *tmp_args)
    self.pop_stmts()
    
  def p_args(self, p):
    '''args : empty
            | args ',' expr
            | expr
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
    p[0] = Decl(p[2])

  def p_init(self, p):
    '''init : VAR ID '=' expr'''
    p[0] = Init(p[2], p[4])
    if self.debug:
      print('Init: {0} = {1}'.format(p[2], p[4]))

  def p_assign(self, p):
    '''assign : ID '=' expr
              | ID '.' ID '=' expr
              | ID '[' expr ']' '=' expr
    '''
    if p[2] == '=':
      p[0] = Assign(p[1], p[3])
    if p[2] == '.':
      p[0] = Assign(p[1], p[5], field=p[3])
    if p[2] == '[':
      p[0] = Assign(p[1], p[6], field=p[3])
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
      arr[-1] = -1
      p[0] = arr
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
      p[0] = copy.deepcopy(p[3])
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
                 | NOT rel_expr
    '''
    if len(p) > 3 and p[2] in '&&||':
      func = And if p[2] == '&&' else Or
      p[0] = Op(func, p[1], p[3])
      if self.debug:
        print('Op: {0} {1} {2}'.format(p[1], p[2], p[3]))
    elif p[1] == '!':
      p[0] = Op(Not, p[2])
      if self.debug:
        print('Op: !{0}'.format(p[2]))
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
      p[0] = Op(func, p[1], p[3])
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
      p[0] = Op(func, p[1], p[3])
    else:
      p[0] = p[1]

  def p_mult_expr(self, p):
    '''mult_expr : operand
                 | mult_expr '*' operand
                 | mult_expr '/' operand
    '''
    if len(p) > 2 and p[2] in '*/':
      func = Mult if p[2] == '*' else Div
      p[0] = Op(func, p[1], p[3])
    else:
      p[0] = p[1]

  def p_operand(self, p):
    '''operand : constant 
               | var_access
               | '(' bool_expr ')'
    '''
    if len(p) > 2:
      p[0] = p[2]
    else:
      p[0] = p[1]

  def p_var_access(self, p):
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

  def p_constant(self, p):
    '''constant : INT
                | STRING_LITERAL
                | TRUE
                | FALSE
    '''
    p[0] = Literal(p[1])

  def p_maybe_newline(self, p):
    '''maybe_newline : empty
                     | maybe_newline NEWLINE
    '''
    pass

  def p_empty(self, p):
    'empty :'
    pass

  def p_error(self, p):
    print('ERROR: {0}'.format(p))


'''
# Main
#print(sys.argv)
if len(sys.argv) >= 2:
  src_lines = ''
  with open(sys.argv[1], 'r') as src:
   src_lines = ''.join(src.readlines()) 
  #print(src_lines)
  if self.debug:
    yacc.parse(src_lines, debug=log)
  else:
    yacc.parse(src_lines)
  #_print_stmts(root)
  root.exe(root_scope)
  #print(root_scope)

else:
  print('usage: ./parser [filename]')
'''
