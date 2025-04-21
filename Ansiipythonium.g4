grammar Ansiipythonium;		
prog:	(statement | fun_decl | class_decl | struct_decl)+ EOF ;
expr: orexpr;
orexpr: xorexpr (OR xorexpr)*;
xorexpr: andexpr (XOR andexpr)?;
andexpr: notexpr (AND notexpr)*;
notexpr: NOT? compexpr;
compexpr: multexpr (('<' | '>' | '=<' | '>=' | '!=' | '==') multexpr)*;
multexpr: addexpr (('*'|'/') addexpr)*;
addexpr: minusexpr (('+'|'-') minusexpr)*;
minusexpr: ('+'|'-')* primaryexpr;
primaryexpr:  funcallexpr | '(' expr ')' | literal;
funcallexpr: '(' ID (',' expr)* ')';
literal: INT | DOUBLE | TRUE | FALSE | ID | STRING;
statement:  expr ';'
    |       var_decl ';'
    |       var_ass ';'
    |       if_statement
    |       for_statement
    |       print ';'
    |       read ';'
    ;

var_decl: type ID ASSIGNMENT expr;
var_ass:  ID ASSIGNMENT expr;
if_statement: 'if' '(' expr ')' stat_block (':' stat_block)?;
for_statement: 'for' '(' (var_decl | var_ass) ';' expr ';' expr ')' stat_block;
stat_block: '{' statement* '}';
fun_decl: type ID '(' arg_decl? (',' arg_decl)* ')' stat_block;
arg_decl: type ID;
class_decl: 'class' ID '{' field* fun_decl* '}'; //Muszą być najpierw pola
struct_decl: 'structure' ID '{' field* '}';
field: type ID ';';

print: '<=' expr;
read:  '=>' ID;

type: type_identifier matrix_identifier?;
type_identifier: INTEGER
    |            FLOAT32
    |            FLOAT64
    |            BOOLEAN
    |            ID
    |            STRING_KEYWORD;
matrix_identifier: vector_identifier vector_identifier?;
vector_identifier: '[' INT ']';
INTEGER : 'integer';
FLOAT32 : 'single_precision';
FLOAT64 : 'double_precision';
BOOLEAN : 'boolean';
STRING_KEYWORD : 'text';
STRING  : QUOTE (ESCAPE | ~'"')* QUOTE;
fragment ESCAPE : '\\"';
fragment QUOTE  : '"';
ASSIGNMENT  : '<-';
NEWLINE : [\r\n]+ -> skip;
WS      : [\p{White_Space}]+ -> channel(HIDDEN);
INT     : [0-9]+ ;
DOUBLE  : [0-9]+ '.' [0-9]+;
TRUE    : 'positive';
FALSE   : 'negative';
AND     : 'AND';
OR      : 'OR';
NOT     : 'NOT';
XOR     : 'XOR';
ID      : [\p{Alpha}][\p{Alnum}]*;
