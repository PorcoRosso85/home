```go
/**
 * Constructor, the returned database must be closed after use.
 *
 * @param engine:  'mem' is for the in-memory non-persistent engine.
 *                 'sqlite', 'rocksdb' and maybe others are available,
 *                 depending on compile time flags.
 * @param path:    path to store the data on disk,
 *                 may not be applicable for some engines such as 'mem'
 * @param options: defaults to nil, ignored by all the engines in the published NodeJS artefact
 */
func New(engine string, path string, options Map) (CozoDB, error)

/**
 * You must call this method for any database you no longer want to use:
 * otherwise the native resources associated with it may linger for as
 * long as your program runs. Simply `delete` the variable is not enough.
 */
func (db *CozoDB) Close()

/**
 * Runs a query
 *
 * @param query: the query
 * @param params: the parameters as key-value pairs, defaults to {} if nil
 */
func (db *CozoDB) Run(query string, params Map) (NamedRows, error)

/**
 * Export several relations
 *
 * @param relations:  names of relations to export, in an array.
 */
func (db *CozoDB) ExportRelations(relations []string) (Map, error)

/**
 * Import several relations
 *
 * Note that triggers are _not_ run for the relations, if any exists.
 * If you need to activate triggers, use queries with parameters.
 *
 * @param data: in the same form as returned by `exportRelations`. The relations
 *              must already exist in the database.
 */
func (db *CozoDB) ImportRelations(payload Map) error

/**
 * Backup database
 *
 * @param path: path to file to store the backup.
 */
func (db *CozoDB) Backup(path string) error

/**
 * Restore from a backup. Will fail if the current database already contains data.
 *
 * @param path: path to the backup file.
 */
func (db *CozoDB) Restore(path string) error

/**
 * Import several relations from a backup. The relations must already exist in the database.
 *
 * Note that triggers are _not_ run for the relations, if any exists.
 * If you need to activate triggers, use queries with parameters.
 *
 * @param path: path to the backup file.
 * @param relations: the relations to import.
 */
func (db *CozoDB) ImportRelationsFromBackup(path string, relations []string) error
```

Tutorial
This tutorial will teach you the basics of using the Cozo database.

There are several ways you can run the queries in this tutorial:

You can run the examples in your browser without installing anything: just open Cozo in Wasm and you are ready to go.

You can download the appropriate cozo-* executable for your operating system from the release page, uncompress, rename to cozo, and run the REPL mode by running in a terminal cozo repl and follow along.

If you are familiar with the Python datascience stack, you should following the instruction here instead to run this notebook in Jupyter Lab, with the notebook file.

There are many other ways, but the above ones are the easiest.

The following cell is to set up Jupyter. Ignore if you are using other methods.

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

%load_ext pycozo.ipyext_direct
Introduction
Datalog is pattern matching for your data.

This sort of thing (Ruby):

config = {db: {user: 'admin', password: 'abc123'}}

case config
in db: {user:} # matches subhash and puts matched value in variable user
  puts "Connect with user '#{user}'"
in connection: {username: }
  puts "Connect with user '#{username}'"
else
  puts "Unrecognized structure of config"
end
# Prints: "Connect with user 'admin'"
Broadly speaking, you provide some values and variables that constitute a pattern for pulling apart some data structure. The matching simultaneously chooses an execution path and gets values of the variables that match out of the data structure.

First steps
Cozo is a relational database. Relations are similar to tables in SQL. The difference is that you can’t have duplicate rows in a relation.

You can define and then retrieve all the rows from a relation in Cozo like this:

?[] <- [['hello', 'world', 'Cozo!']]
 	_0	_1	_2
0	hello	world	Cozo!
This is a rule. The <- separates the head of the rule on the left from the body on the right. The [] <- acts like SELECT * in SQL. The above query in SQL would look something like:

SELECT * FROM (VALUES(‘hello’, ‘world’, ‘sql’)) as unnecessary_alias;
(a hint here of Datalog’s freedom from the endless ceremony that plagues SQL)

You can have multiple rows:

?[] <- [[1, 2, 3], ['a', 'b', 'c']]
 	_0	_1	_2
0	1	2	3
1	a	b	c
You can have the usual sorts of types:

?[] <- [[1.5, 2.5, 3, 4, 5.5],
        ['aA', 'bB', 'cC', 'dD', 'eE'],
        [true, false, null, -1.4e-2, "A string with double quotes"]]
 	_0	_1	_2	_3	_4
0	True	False	None	-0.014000	A string with double quotes
1	1.500000	2.500000	3	4	5.500000
2	aA	bB	cC	dD	eE
The input literal representations are similar to those in JavaScript. In particular, strings in double quotes are guaranteed to be interpreted in the same way as in JSON. The output are in JSON, but how they appear on your screen depends on your setup. For example, if you are using a Python setup, booleans are displayed as True and False instead of in lowercase, since they are converted to the native Python datatypes for display.

In the last example, you may have noticed that the returned order is not the same as the input order. This is because in Cozo relations are always stored as trees, and trees are always sorted.

Another consequence of relations as trees is that you can have no duplicate rows:

?[] <- [[1], [2], [1], [2], [1]]
 	_0
0	1
1	2
Expressions
The next example shows the use of various functions, expressions and comments:

?[] <- [[
            1 + 2, # addition
            3 / 4, # division
            5 == 6, # equality
            7 > 8, # greater
            true || false, # or
            false && true, # and
            lowercase('HELLO'), # function
            rand_float(), # function taking no argument
            union([1, 2, 3], [3, 4, 5], [5, 6, 7]), # variadic function
        ]]
 	_0	_1	_2	_3	_4	_5	_6	_7	_8
0	3	0.750000	False	False	True	False	hello	0.061268	[1, 2, 3, 4, 5, 6, 7]
Cozo has a pretty robust set of built-in functions and operators.
