#include "ast.h"
int exe_int(ast_expr expr){
	return ((int (*)(int, void **))expr.op)(expr.argc, expr.argv);
}
int exe_truthy(ast_expr expr){return exe_int(expr);}

int b_and(ast_expr l, ast_expr r){
	return exe_truthy(l) && exe_truthy(r);
}
int b_or(ast_expr l, ast_expr r){
	return exe_truthy(l) || exe_truthy(r);
}
int b_not(ast_expr e){
	return !exe_truthy(e);
}

int m_add(ast_expr l, ast_expr r){
	return exe_int(l) + exe_int(r);
}
int m_sub(ast_expr l, ast_expr r){
	return exe_int(l) - exe_int(r);
}
int m_mult(ast_expr l, ast_expr r){
	return exe_int(l) * exe_int(r);
}
int m_div(ast_expr l, ast_expr r){
	return exe_int(l) / exe_int(r);
}
