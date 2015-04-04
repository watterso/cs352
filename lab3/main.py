import os
import sys

from parser import MiniScriptParser

def _print_stmts(stmt, indent=0):
  print('{0}{1}'.format(' '*2*indent, stmt))
  if hasattr(stmt,'stmts') and stmt.stmts:
    for st in stmt.stmts:
      _print_stmts(st, indent+1)
  if hasattr(stmt,'soit') and stmt.soit:
    print(' '*2*indent+'else:')
    _print_stmts(stmt.soit,indent)

def _code(filename):
  with open(filename, 'r') as src:
    return ''.join(src.readlines())


def main(args, run):
  if len(args) >= 2:
    code = _code(args[1]) 
    debug = int(args[2]) if len(args) > 2 and args[2] else 0
    p = MiniScriptParser(debug)
    stmt, scope = p.parse(code)
    if debug:
      print('====== Output ======')
    if run:
      stmt.exe(scope)
    else:
      _print_stmts(stmt) 
  else:
    print('usage: ./parser filename <debug>')

if __name__ == '__main__':
  #print('{0} ? {1}'.format(os.path.basename(__file__), os.path.basename(__file__) == 'parser'))
  main(sys.argv, os.path.basename(__file__) == 'parser')
