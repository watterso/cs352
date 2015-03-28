import sys

import lib.lex as lex

class MiniScriptLexer:
  # tokens I pass through literally
  literals = '=+-*/:;.,()[]{}'

  # reserved words
  reserved = {
    'if':'I_COND',
    'else': 'E_COND',
    'while': 'WHILE',
    'do': 'DO',
    'var': 'VAR',
    'true': 'TRUE',
    'false': 'FALSE',
  }

  # defined tokens
  tokens = [
      'START', 'END',
      'ID', 'INT', 'STRING_LITERAL',
      'NEWLINE', 'WRITE',
      'EQ', 'NE', 'GTE', 'LTE', 'GT', 'LT',
      'AND', 'OR', 'NOT'  
      ] + reserved.values()

  t_START = r'<script\ type="text/JavaScript">'
  t_END = r'</script>'

  def t_WRITE(self, t):
    r'document.write'
    return t


  t_ignore  = ' \t'
  
  t_OR = r'\|\|'
  t_AND = r'&&'
  t_NOT = r'!'
  t_LT = r'<'
  t_GT = r'>'
  t_LTE = r'<='
  t_GTE = r'>='
  t_EQ = r'=='
  t_NE = r'!='

  def t_ID(self, t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    t.type = self.reserved.get(t.value,'ID')
    return t

  def t_INT(self, t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

  def t_STRING_LITERAL(self, t):
    r'\"[^\n^\"]*\"'
    t.value = t.value[1:-1]
    return t

  def t_NEWLINE(self, t):
    r'\n'
    t.lexer.lineno += 1
    return t

  def t_error(self, t):
    print(t)
    print('syntax error\n')
    sys.exit(0)
  
  def build(self,**kwargs):
    self.lexer = lex.lex(module=self, **kwargs)

  def test(self,data):
    self.lexer.input(data)
    while True:
      tok = self.lexer.token()
      if not tok: break
      print(tok)
