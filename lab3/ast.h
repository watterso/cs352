enum ast_type{
	a_if,
	a_while,
	a_do,
	a_block,
	a_expr
};
typedef struct {
	void * prev;
	void * next;
	ast_type type;
	void * node;
} ast_node;
typedef struct {
	ast_node a_else;    //go here if condition evaluates false if NULL, go to next
	ast_node condition; //conditional code to be evaluated
	ast_node block;     //code to be executed
} ast_if;
typedef struct {
	ast_node condition; //conditional code to be evaluated
	ast_node block;     //code to be repeated
} ast_while;
typedef struct {
	ast_node condition; //conditional code to be evaluated
	ast_node block;     //code to be exe'd once then conditionally repeated
} ast_do;
typedef struct {
	ast_node start;
	ast_node end;
} ast_block;
typedef struct {
	void (* op)(int, void**);
	int argc;
	void ** argv;
} ast_expr;
