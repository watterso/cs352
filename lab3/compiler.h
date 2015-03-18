#include <string.h>
#include <map>
typedef struct {
	int num;
	char* ptr;
	int which_val;
	int lineno;
} YYSTYPE;
#define YYSTYPE_IS_DECLARED
typedef struct {
	int num;
	char* ptr;
	int which_val;
	int defined;
} Variable;
struct cmp_str
{
	bool operator()(const char *a, const char *b) const
	{
		return strcmp(a, b) < 0;
	}
};
typedef std::map<char*,Variable,cmp_str>SymbolTable;
typedef std::map<int,Variable>OmniArray;
