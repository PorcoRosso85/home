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

Find values for these variables
More complex queries proceed by providing some expressions with values and variables, much like pattern matching in your favourite language.

Cozo tries to find all the sets of rows that match the given values, including values for the variables that also match across all the expressions. Some examples will make this clearer.

?[first, second, third] <- [[1, 2, 3], ['a', 'b', 'c']]
 	first	second	third
0	1	2	3
1	a	b	c
Here, we’ve just provided named variables for the values coming back.

Note that you have to do obvious things, like not having different numbers of columns within one relation. Typing can be strict or loose as you choose (so far, it’s all been loose; we’ll see examples of strict typing shortly).

For <- (called constant) rules, the number of bindings must match the actual data (the arity), otherwise, you will get an error:

?[first, second] <- [[1, 2, 3], ['a', 'b', 'c']]
parser::fixed_rule_head_arity_mismatch

  × Fixed rule head arity mismatch
   ╭─[1:1]
 1 │ ?[first, second] <- [[1, 2, 3], ['a', 'b', 'c']]
   · ─────────────────────────────────────────────────
 2 │
   ╰────
  help: Expected arity: 3, number of arguments given: 2

Now let’s define rules that apply (use) other rules:

rule[first, second, third] <- [[1, 2, 3], ['a', 'b', 'c']]
?[a, b, c] := rule[a, b, c]
 	a	b	c
0	1	2	3
1	a	b	c
You’ll notice the two different connectors. The first, <-, is actually syntactic sugar for <~, which is used for invoking functions on the right hand side (as well as Cozo’s many built-in functions, you can write your own in the host language). <- is invoking a Constant function that looks like rule[first, second, third] <~ Constant(data: [[1, 2, 3], ['a', 'b', 'c']]) <- and <~ rules are called constant rules.

The second rule is an inline rule, meaning it’s not invoking anything external to the database; it’s just matching data. Note that because it is named ?, it is the result of the query.

Note how in the second line, we match a, b, c to the first, second, third in the first rule.

We don’t have to use all the variables from the body in an inline rule:

rule[first, second, third] <- [[1, 2, 3], ['a', 'b', 'c']]
?[c, b] := rule[a, b, c]
 	c	b
0	3	2
1	c	b
Let’s get a bit fancier:

?[c, b] := rule[a, b, c], is_num(a)
rule[first, second, third] <- [[1, 2, 3], ['a', 'b', 'c']]
 	c	b
0	3	2
Here, the first rule had multiple bodies, separated by commas. These are effectively joined by and. We see here how the variable a matches with a value from the database, but also has to return true when passed to the is_num function.

You can also bind constants to rule applications directly:

rule[first, second, third] <- [[1, 2, 3], ['a', 'b', 'c']]
?[c, b] := rule['a', b, c]
 	c	b
0	c	b
The pattern in the head on the second line matches only rows with an ‘a’ for the first field value.

You can have multiple rules with the same head name, which is like joining their bodies with OR.

important[a] := recent[a], unread[a], not deleted[a]
important[a] := flagged[a], not deleted[a]
This means a is important if it isn’t deleted, and it’s either flagged, or recent and unread. You can also use ‘and’, ‘or’, ‘not’ and parentheses, although the style above is more idiomatic.

We can just directly set a value as part of the query, using ‘=’:

rule[first, second, third] <- [[1, 2, 3], ['a', 'b', 'c']]
?[c, b, d] := rule[a, b, c], is_num(a), d = a + b + 2*c
 	c	b	d
0	3	2	9
The unification = unifies with a single value. Use in to unify with each value within a list in turn:

?[x, y] := x in [1, 2, 3], y in ['x', 'y']
 	x	y
0	1	x
1	1	y
2	2	x
3	2	y
4	3	x
5	3	y
Having multiple rule applications in the body generates every combination of the bindings:

r1[] <- [[1, 'a'], [2, 'b']]
r2[] <- [[2, 'B'], [3, 'C']]

?[l1, l2] := r1[a, l1],
             r2[b, l2]
 	l1	l2
0	a	B
1	a	C
2	b	B
3	b	C
This is a cross join in SQL

We’ve now seen enough of the basics to start looking at some more complex operations.

Joins, made easy
r1[] <- [[1, 'a'], [2, 'b']]
r2[] <- [[2, 'B'], [3, 'C']]

?[l1, l2] := r1[a, l1],
             r2[a, l2] # reused `a`
 	l1	l2
0	b	B
A join is as simple as using the same variable in different relations. Here, we are asking for a single value of a that matches a row in each of the sources at the same time.

Compare the above with the SQL for the same operation:

WITH
    r1 AS SELECT * FROM (VALUES (1, ‘a’), (2, ‘b’)) as t(c1, c2),
    r2 AS SELECT * FROM (VALUES(2, ‘B’), (3, ‘C’)) as u(d1, d2)
SELECT
    r1.c2, r2.d2 FROM r1 JOIN r2 ON (r1.c1 = r2.d1);
An outer join is done by considering the cases separately:

a[x, y] <- [[1, 2], [3, 4]]
b[y, z] <- [[2, 3], [2, 4]]
?[x, y, z] := a[x, y], b[y, z]
?[x, y, z] := a[x, y], not b[y, _], z = null
 	x	y	z
0	1	2	3.000000
1	1	2	4.000000
2	3	4	nan
Note that we still only have a single output ? rule here; it is split into two parts effectively joining the right sides with or as we discussed previously.

Stored relations
The relations we’ve seen so far were created on the fly as constant rules, and only persist for the duration of the query.

You can of course also persist data. To do this, you first declare the relation:

:create stored {c1, c2}
 	status
0	OK
This creates a relation called ‘stored’ with two columns that will take any type. Here is a fully typed relation:

:create dept_info {
    company_name: String,
    department_name: String,
    =>
    head_count: Int default 0,
    address: String,
}
 	status
0	OK
This should be fairly obvious, except for the => in the middle. This symbol separates the columns in the primary key before the => from the other columns. If the => isn’t present, all of the columns are considered part of the primary key.

?[a, b, c] <- [[1, 'a', 'A'],
[2, 'b', 'B'],
[3, 'c', 'C'],
[4, 'd', 'D']]

:create fd {a, b => c}
 	status
0	OK
?[a, b, c] := *fd[a, b, c]
 	a	b	c
0	1	a	A
1	2	b	B
2	3	c	C
3	4	d	D
Note how we create rows in fd as we define it.

In Cozo terms, the fields after the => are functionally dependent on the ones before. Those before determine identity, which lets the :put operation function as (upsert)https://wiki.postgresql.org/wiki/UPSERT.

?[a, b, c] <- [[3, 'c', 'CCCCCCC']]

:put fd {a, b => c}
 	status
0	OK
?[a, b, c] := *fd[a, b, c]
 	a	b	c
0	1	a	A
1	2	b	B
2	3	c	CCCCCCC
3	4	d	D
Note that the name of the stored relation should not start with an underscore _. You will get no error if you use a name starting with an underscore, but you will discover that the relation won’t be persisted. What you are dealing with is actually what is called an ephemeral relation.

You can see the stored relations in your system by running a system op:

::relations
 	name	arity	access_level	n_keys	n_non_keys	n_put_triggers	n_rm_triggers	n_replace_triggers	description
0	dept_info	4	normal	2	2	0	0	0	
1	fd	3	normal	2	1	0	0	0	
2	stored	2	normal	2	0	0	0	0	
Note that we have regular operations like :create that start with a :, and system operations with a ::.

We can investigate the columns of the stored relation:

::columns stored
 	column	is_key	index	type	has_default
0	c1	True	0	Any?	False
1	c2	True	1	Any?	False
Stored relations can be accessed by using an asterisk * before the name:

?[a, b] := *stored[a, b]
 	a	b
Unlike relations defined inline, the columns of stored relations have fixed names. You can take advantage of this by selectively referring to columns by name, especially if you have a lot of columns:

?[a, b] := *stored{l2: b, l1: a}
eval::named_field_not_found

  × stored relation 'stored' does not have field 'l1'
   ╭─[1:1]
 1 │ ?[a, b] := *stored{l2: b, l1: a}
   ·            ─────────────────────
 2 │
   ╰────

If the binding is the same as the column name, you can omit the binding:

?[l2] := *stored{l2}
eval::named_field_not_found

  × stored relation 'stored' does not have field 'l2'
   ╭─[1:1]
 1 │ ?[l2] := *stored{l2}
   ·          ───────────
 2 │
   ╰────

Use :rm to remove data:

?[l1, l2] <- [['e', 'E']]

:rm stored {l1, l2}
eval::required_col_not_found

  × required column l1 not found

?[l1, l2] := *stored[l1, l2]
 	l1	l2
Use ::remove (double colon!) to get rid of a stored relation:

::remove stored
 	status
0	OK
::relations
 	name	arity	access_level	n_keys	n_non_keys	n_put_triggers	n_rm_triggers	n_replace_triggers	description
0	dept_info	4	normal	2	2	0	0	0	
1	fd	3	normal	2	1	0	0	0	
We’ve now seen a variety of Cozo queries. They all have one or more rules, one of which will have the name ? which determines which variables are the result of the query.

A query can also have one or more operations such as :put, which are executed after the query and can use its results. These operations might also change the query in some way, by limiting the number of results, sorting, paginating and so on.

Stored relations can have triggers. These are discussed in detail here.

Before continuing, let’s remove the stored relation we introduced:

::remove fd
 	status
0	OK
Command blocks
Cozo executes the entire script you send to it in a single transaction. You can do multiple query-command blocks by wrapping each block in curly braces. The blocks are executed in sequence and either all of them succeed or none of them do and the state rolls back. The result returned to a client is whatever is in the last block. Like this:

{?[a] <- [[1], [2], [3]]; :replace test {a}}
{?[a] <- []; :replace test2 {a}}
%swap test test2
%return test
Graphs
Now let’s consider a graph stored as a relation:

?[loving, loved] <- [['alice', 'eve'],
                     ['bob', 'alice'],
                     ['eve', 'alice'],
                     ['eve', 'bob'],
                     ['eve', 'charlie'],
                     ['charlie', 'eve'],
                     ['david', 'george'],
                     ['george', 'george']]

:replace love {loving, loved}
 	status
0	OK
The graph we have created reads like “Alice loves Eve, Bob loves Alice”, “nobody loves David, David loves George, but George only loves himself”, and so on. Here we used :replace instead of :create. The difference is that if love already exists, it will be wiped and replaced with the new data given.

We can investigate competing interests:

?[loved_by_b_e] := *love['eve', loved_by_b_e],
                   *love['bob', loved_by_b_e]
 	loved_by_b_e
0	alice
It fells natural here to use the or keyword:

?[loved_by_b_e] := *love['eve', loved_by_b_e] or *love['bob', loved_by_b_e],
                   loved_by_b_e != 'bob',
                   loved_by_b_e != 'eve'
 	loved_by_b_e
0	alice
1	charlie
Compare this with multiple rule definitions under the same name:

?[loved_by_b_e] := *love['eve', loved_by_b_e],
                   loved_by_b_e != 'bob',
                   loved_by_b_e != 'eve'
?[loved_by_b_e] := *love['bob', loved_by_b_e],
                   loved_by_b_e != 'bob',
                   loved_by_b_e != 'eve'
 	loved_by_b_e
0	alice
1	charlie
When you have multiple definitions of the same inline rule, the rule heads must be compatible. Only inline rules can have multiple definitions.

Negation
Negation of expressions should be familiar:

?[loved] := *love[person, loved], !ends_with(person, 'e')
 	loved
0	alice
1	george
Rule applications can also be negated, not with the ! operator, but with the not keyword:

?[loved_by_e_not_b] := *love['eve', loved_by_e_not_b],
                       not *love['bob', loved_by_e_not_b]
 	loved_by_e_not_b
0	bob
1	charlie
There are two sets of logical operations in Cozo, one set that acts on the level of expressions, and another set that acts within the expression (we say they work on atoms):

For atoms: , or and (conjunction), or (disjunction), not (negation)

For expressions: && (conjunction), || (disjunction), ! (negation)

The difference between , and and is operator precedence: and has higher precedence than or, whereas , has lower precedence than or.

There is a safety rule for negation:

?[not_loved_by_b] := not *love['bob', not_loved_by_b]
eval::unbound_symb_in_head

  × Symbol 'not_loved_by_b' in rule head is unbound
   ╭─[1:1]
 1 │ ?[not_loved_by_b] := not *love['bob', not_loved_by_b]
   ·   ──────────────
 2 │
   ╰────
  help: Note that symbols occurring only in negated positions are not considered bound

This query is forbidden because the resulting relation is infinite. For example, ‘gold’ should be in the result, since according to the facts stored in the database, Bob has no interest in ‘gold’.

To make our query finite, we have to explicitly give our query a closed world:

the_population[p] := *love[p, _a]
the_population[p] := *love[_a, p]

?[not_loved_by_b] := the_population[not_loved_by_b],
                     not *love['bob', not_loved_by_b]
 	not_loved_by_b
0	bob
1	charlie
2	david
3	eve
4	george
Recursion
The single greatest advantage of Datalog over SQL is that recursive/graph queries area much simpler.

Inline rules can apply other rules, and can have multiple definitions. If you combine these two, you get recursions:

alice_love_chain[person] := *love['alice', person]
alice_love_chain[person] := alice_love_chain[in_person],
                            *love[in_person, person]

?[chained] := alice_love_chain[chained]
 	chained
0	alice
1	bob
2	charlie
3	eve
You may object that you only need to be able to apply other rules to have recursion, without multiple definitions. Technically correct, but the resulting queries are not useful:

..
alice_love_chain[person] := alice_love_chain[in_person],
                            *love[in_person, person]

?[chained] := alice_love_chain[chained]
 	chained
Similar to the negation case, if there is no way to deduce a fact from the given facts, then the fact itself is considered false. You need multiple definitions to “bootstrap” the query.

Aggregation
Aggregations are usually used to compute statistics. In Cozo, aggregations are applied in the head of inline rules:

?[person, count(loved_by)] := *love[loved_by, person]
 	person	count(loved_by)
0	alice	2
1	bob	1
2	charlie	1
3	eve	2
4	george	2
The usual sum, mean, etc. are all available.

Here is the full list of aggregations for you to play with.

Query options
We have seen query options like :create, :put, :rm for manipulating stored relations. There are also query options for controlling what is returned:

?[loving, loved] := *love{ loving, loved }

:limit 1
 	loving	loved
0	alice	eve
Next we want the result to be sorted by loved in descending order, then loving in ascending order, and skip the first row:

?[loving, loved] := *love{ loving, loved }

:order -loved, loving
:offset 1
 	loving	loved
0	george	george
1	alice	eve
2	charlie	eve
3	eve	charlie
4	eve	bob
5	bob	alice
6	eve	alice
Putting - in front of variables in :order clause denotes reverse order. Nothing or + denotes the ascending order.

The full list of query options are explained in this chapter.

Fixed rules
We’ve seen how the <- syntax for constant rules is syntax sugar. The full syntax is:

?[] <~ Constant(data: [['hello', 'world', 'Cozo!']])
 	_0	_1	_2
0	hello	world	Cozo!
Here we are using the fixed rule Constant, which takes one option named data. The curly tail <~ denotes a fixed rule.

Fixed rules take input relations as arguments, apply custom logic to them and produce its output relation. They’re functions that return relations, defined outside the Cozo engine itself (either built-in or loaded from a library or defined by the host language).

The Constant fixed rule take zero input relations.

If you are using Cozo in browser, Constant is the only fixed rule you can use. In all other cases your Cozo would have the graph algorithms module enabled, and all graph algorithms are implemented as fixed rules. As an example, let’s find out who is most popular in the love graph by using the PageRank algorithm:

?[person, page_rank] <~ PageRank(*love[])

:order -page_rank
 	person	page_rank
0	george	0.280443
1	eve	0.275376
2	alice	0.191205
3	bob	0.103023
4	charlie	0.103023
5	david	0.025000
Here the input relation is the stored relation *love (as noted above, you will receive an error if you run this in the WASM implementation).

Each fixed rule is different: here is the full list.

::remove love
 	status
0	OK
Time travel
A very useful capability of Cozo is the ability to time travel in a stored relation. Usually when you :put into a relation, the old value is overwritten; and when you :rm, the row is completely gone. But the old values can be of great value — we have a short story about it.

In this case, time travel is the solution: instead of storing current facts, the stored relation stores the complete history of facts, at least all the available history as history itself unfolds.

If you believe that you don’t want this functionality at all, you can skip to the next section. At Cozo we adopt the “zero-cost, zero-mental-overhead abstraction” philosophy: if you don’t use a functionality, you don’t pay the performance or cognitive overhead.

Let’s have a simple example: storing the head of state of countries. First we have to create a new stored relation:

:create hos {state: String, year: Validity => hos: String}
 	status
0	OK
hos is shorthand for “head of state”. The only thing different about this relation is that we are giving year the type Validity. You can think of validity as a list of two elements, the first element being an integer and the second element being a boolean. The integer indicates the “time” of the fact recorded by the row, the boolean, if true, indicates that the new version of the row holds starting from the indicated time; if the boolean is false, the row is deleted at this time.

Note that the integer only identifies a temporal sequence to Cozo. What sequence you use is up to you. UNIX Epoch is the default, as we will see.

Now let’s insert some data:

?[state, year, hos] <- [['US', [2001, true], 'Bush'],
                        ['US', [2005, true], 'Bush'],
                        ['US', [2009, true], 'Obama'],
                        ['US', [2013, true], 'Obama'],
                        ['US', [2017, true], 'Trump'],
                        ['US', [2021, true], 'Biden']]

:put hos {state, year => hos}
 	status
0	OK
It is OK to assert a still valid fact again, as we have done above. You can use this relation like a normal relation:

?[state, year, hos] := *hos{state, year, hos}
 	state	year	hos
0	US	[2021, True]	Biden
1	US	[2017, True]	Trump
2	US	[2013, True]	Obama
3	US	[2009, True]	Obama
4	US	[2005, True]	Bush
5	US	[2001, True]	Bush
The curious thing is that it is sorted descendingly by year. Validity sorts descendingly.

For any stored relation that has type Validity at the last slot of the key, the time-travel capability is enabled. Say you have forgotten who the president of the US was in 2019. Easy:

?[hos, year] := *hos{state: 'US', year, hos @ 2019}
 	hos	year
0	Trump	[2017, True]
In your answer you also got the year that this fact was last known to be true.

You also don’t know about the year 2099:

?[hos, year] := *hos{state: 'US', year, hos @ 2099}
 	hos	year
0	Biden	[2021, True]
That certainly doesn’t look right. Let’s fix it by retracting facts on or after 2025, and only inserting them back when we have the sure facts:

?[state, year, hos] <- [['US', [2025, false], '']]

:put hos {state, year => hos}
 	status
0	OK
As we have hinted, you retract facts by putting a retraction. Now let’s run the query again:

?[hos, year] := *hos{state: 'US', year, hos @ 2099}
 	hos	year
Since the database does not contain facts on or after 2025, your query returns empty.

This functionality is flexible: you can mix different periods in the same query:

?[hos2018, hos2010] := *hos{state: 'US', hos: hos2018 @ 2018},
                       *hos{state: 'US', hos: hos2010 @ 2010}
 	hos2018	hos2010
0	Trump	Obama
As the relation hos is just a normal relation, you can still rm facts from it, in which case the facts are irretrievably gone. Whether that’s desirable is up to you: the database gives you the choice of how you want to use it, and trusts that you know how to use it correctly for your use case.

First let’s create a new stored relation to store people’s moods:

:create mood {name: String, at: Validity => mood: String}
 	status
0	OK
I want to record my mood now:

?[name, at, mood] <- [['me', 'ASSERT', 'curious']]
:put mood {name, at => mood}
 	status
0	OK
Instead of giving a list of two elements as we have done above, we have simply used the string ASSERT, and the system will know that we mean an assertion of a current fact, and you guessed it, the value used is the current UNIX Epoch.

?[name, at, mood] := *mood{name, at, mood}
 	name	at	mood
0	me	[1700569902203327, True]	curious
?[name, time, mood] := *mood{name, at, mood},
                       time = format_timestamp(at)
 	name	time	mood
0	me	2023-11-21T12:31:42.203+00:00	curious
To query for current facts, use the string NOW in the validity specification:

?[name, time, mood] := *mood{name, at, mood @ 'NOW'},
                       time = format_timestamp(at)
 	name	time	mood
0	me	2023-11-21T12:31:42.203+00:00	curious
You can put in facts with manual timestamps as before, so it is possible that your database contains facts about the future. Let’s do just that. Instead of giving a mysterious string of numerals, you can use a string for the timestamp:

?[name, at, mood] <- [['me', '2030-01-01T00:00:00.000+00:00', 'hopeful']]
:put mood {name, at => mood}
 	status
0	OK
Since this is in the future, it shouldn’t affect NOW:

?[name, time, mood] := *mood{name, at, mood @ 'NOW'},
                       time = format_timestamp(at)
 	name	time	mood
0	me	2023-11-21T12:31:42.203+00:00	curious
In this case, there is also END for the validity specification, meaning to extract facts at the end of time:

?[name, time, mood] := *mood{name, at, mood @ 'END'},
                       time = format_timestamp(at)
 	name	time	mood
0	me	2030-01-01T00:00:00+00:00	hopeful
Retraction at the current timestamp can be done with the string RETRACT:

?[name, at, mood] <- [['me', 'RETRACT', '']]
:put mood {name, at => mood}
 	status
0	OK
Retraction placed in the future can also be done with stringy timestamps by prefixing with ~:

?[name, at, mood] <- [['me', '~9999-01-01T00:00:00.000+00:00', 'who cares']]
:put mood {name, at => mood}
 	status
0	OK
Now let’s look at the complete history:

?[name, time, is_assert, mood] := *mood{name, at, mood},
                                  time = format_timestamp(at),
                                  is_assert = to_bool(at)
 	name	time	is_assert	mood
0	me	2023-11-21T12:31:42.203+00:00	True	curious
1	me	2023-11-21T12:31:46.232+00:00	False	
2	me	2030-01-01T00:00:00+00:00	True	hopeful
3	me	9999-01-01T00:00:00+00:00	False	who cares
This time-travel facility is much faster than what you get if you try to implement it directly with Datalog: see the note for more details. Some further technical details of time travel is discussed in its own chapter.

::remove mood, hos
 	status
0	OK
Extended example: the air routes dataset
Now you have a basic understanding of using the various constructs of Cozo, let’s deal with a small real-world dataset, with about 3700 nodes and 57000 edges.

The data we are going to use, and many examples that we will present, are adapted from the book Practical Gremlin. Gremlin is an imperative query language for graphs, a very different take compared to Datalog.

First, let’s create the stored relations we want (wrapping queries in braces allows you to execute several queries together atomically):

{:create airport {
    code: String
    =>
    icao: String,
    desc: String,
    region: String,
    runways: Int,
    longest: Float,
    elev: Float,
    country: String,
    city: String,
    lat: Float,
    lon: Float
}}
{:create country {
    code: String
    =>
    desc: String
}}
{:create continent {
    code: String
    =>
    desc: String
}}
{:create contain { entity: String, contained: String }}
{:create route { fr: String, to: String => dist: Float }}
 	status
0	OK
The next command applies only if you are using Jupyter notebooks: it downloads a JSON file containing the data and imports it into the database. The commented out line shows how to do the same thing with a local file. If you are using the Cozo WASM interface, click the “Import from URL” or the “Import from File” icon, and paste in the address.

%cozo_import_remote_file 'https://raw.githubusercontent.com/cozodb/cozo/dev/cozo-core/tests/air-routes.json'
# %cozo_import_local_file '../../cozo/cozo-core/tests/air-routes.json'
If you are using the cozo repl command line, the command to use instead is simply

%import https://raw.githubusercontent.com/cozodb/cozo/dev/cozo-core/tests/air-routes.json
You can replace the URL with the path to a local file as well. Other environments also have ways to do the same thing: refer to the respective documentations.

If you feel that the above is too much magic, we will show you the “hard way” of importing the same data at the end of this tutorial. For now let’s move on.

Let’s verify all the relations we want are there:

::relations
 	name	arity	access_level	n_keys	n_non_keys	n_put_triggers	n_rm_triggers	n_replace_triggers	description
0	airport	11	normal	1	10	0	0	0	
1	contain	2	normal	2	0	0	0	0	
2	continent	2	normal	1	1	0	0	0	
3	country	2	normal	1	1	0	0	0	
4	dept_info	4	normal	2	2	0	0	0	
5	route	3	normal	2	1	0	0	0	
6	test	1	normal	1	0	0	0	0	
7	test2	1	normal	1	0	0	0	0	
While we are at it, let’s lock all these tables to prevent accidentally changing their contents:

::access_level read_only airport, contain, continent, country, route
 	status
0	OK
More information about what this does is explained in this chapter.

Let’s just look at some data. Start with airports:

?[code, city, desc, region, runways, lat, lon] := *airport{code, city, desc, region, runways, lat, lon}

:limit 5
 	code	city	desc	region	runways	lat	lon
0	AAA	Anaa	Anaa Airport	PF-U-A	1	-17.352600	-145.509995
1	AAE	Annabah	Annaba Airport	DZ-36	2	36.822201	7.809170
2	AAL	Aalborg	Aalborg Airport	DK-81	2	57.092759	9.849243
3	AAN	Al Ain	Al Ain International Airport	AE-AZ	1	24.261700	55.609200
4	AAQ	Anapa	Anapa Airport	RU-KDA	1	45.002102	37.347301
Airports with the most runways:

?[code, city, desc, region, runways, lat, lon] := *airport{code, city, desc, region, runways, lat, lon}

:order -runways
:limit 10
 	code	city	desc	region	runways	lat	lon
0	DFW	Dallas	Dallas/Fort Worth International Airport	US-TX	7	32.896801	-97.038002
1	ORD	Chicago	Chicago O'Hare International Airport	US-IL	7	41.978600	-87.904800
2	AMS	Amsterdam	Amsterdam Airport Schiphol	NL-NH	6	52.308601	4.763890
3	BOS	Boston	Boston Logan	US-MA	6	42.364300	-71.005203
4	DEN	Denver	Denver International Airport	US-CO	6	39.861698	-104.672997
5	DTW	Detroit	Detroit Metropolitan, Wayne County	US-MI	6	42.212399	-83.353401
6	ATL	Atlanta	Hartsfield - Jackson Atlanta International Airport	US-GA	5	33.636700	-84.428101
7	GIS	Gisborne	Gisborne Airport	NZ-GIS	5	-38.663300	177.977997
8	HLZ	Hamilton	Hamilton International Airport	NZ-WKO	5	-37.866699	175.332001
9	IAH	Houston	George Bush Intercontinental	US-TX	5	29.984400	-95.341400
How many airports are there in total?

?[count(code)] := *airport{code}
 	count(code)
0	3504
Let’s get a distribution of the initials of the airport codes:

?[count(initial), initial] := *airport{code}, initial = first(chars(code))

:order initial
 	count(initial)	initial
0	212	A
1	235	B
2	214	C
3	116	D
4	95	E
5	76	F
6	135	G
7	129	H
8	112	I
9	80	J
10	197	K
11	184	L
12	228	M
13	111	N
14	89	O
15	203	P
16	7	Q
17	121	R
18	245	S
19	205	T
20	77	U
21	86	V
22	59	W
23	28	X
24	211	Y
25	49	Z
More useful are the statistics of runways:

?[count(r), count_unique(r), sum(r), min(r), max(r), mean(r), std_dev(r)] :=
    *airport{runways: r}
 	count(r)	count_unique(r)	sum(r)	min(r)	max(r)	mean(r)	std_dev(r)
0	3504	7	4980.000000	1	7	1.421233	0.743083
Using country, we can find countries with no airports:

?[desc] := *country{code, desc}, not *airport{country: code}
 	desc
0	Andorra
1	Liechtenstein
2	Monaco
3	Pitcairn
4	San Marino
The route relation by itself is rather boring:

?[fr, to, dist] := *route{fr, to, dist}

:limit 10
 	fr	to	dist
0	AAA	FAC	48.000000
1	AAA	MKP	133.000000
2	AAA	PPT	270.000000
3	AAA	RAR	968.000000
4	AAE	ALG	254.000000
5	AAE	CDG	882.000000
6	AAE	IST	1161.000000
7	AAE	LYS	631.000000
8	AAE	MRS	477.000000
9	AAE	ORN	477.000000
It just records the starting and ending airports of each route, together with the distance. This relation only becomes useful when used as a graph.

Airports with no routes:

?[code, desc] := *airport{code, desc}, not *route{fr: code}, not *route{to: code}
 	code	desc
0	AFW	Fort Worth Alliance Airport
1	APA	Centennial Airport
2	APK	Apataki Airport
3	BID	Block Island State Airport
4	BVS	Breves Airport
5	BWU	Sydney Bankstown Airport
6	CRC	Santa Ana Airport
7	CVT	Coventry Airport
8	EKA	Murray Field
9	GYZ	Gruyere Airport
10	HFN	Hornafjordur Airport
11	HZK	Husavik Airport
12	ILG	New Castle Airport
13	INT	Smith Reynolds Airport
14	ISL	Ataturk International Airport
15	KGG	Kédougou Airport
16	NBW	Leeward Point Field
17	NFO	Mata'aho Airport
18	PSY	Stanley Airport
19	RIG	Rio Grande Airport
20	SFD	San Fernando De Apure Airport
21	SFH	San Felipe International Airport
22	SXF	Berlin-Schönefeld International Airport *Closed*
23	TUA	Teniente Coronel Luis a Mantilla Airport
24	TWB	Toowoomba Airport
25	TXL	Berlin, Tegel International Airport *Closed*
26	VCV	Southern California Logistics Airport
27	YEI	Bursa Yenişehir Airport
Airports with the most out routes:

route_count[fr, count(fr)] := *route{fr}
?[code, n] := route_count[code, n]

:sort -n
:limit 5
 	code	n
0	FRA	310
1	IST	309
2	CDG	293
3	AMS	283
4	MUC	270
How many routes are there from the European Union to the US?

routes[unique(r)] := *contain['EU', fr],
                     *route{fr, to},
                     *airport{code: to, country: 'US'},
                     r = [fr, to]
?[n] := routes[rs], n = length(rs)
 	n
0	435
How many airports are there in the US with routes from the EU?

?[count_unique(to)] := *contain['EU', fr],
                       *route{fr, to},
                       *airport{code: to, country: 'US'}

 	count_unique(to)
0	45
How many routes are there for each airport in London, UK?

?[code, count(code)] := *airport{code, city: 'London', region: 'GB-ENG'}, *route{fr: code}
 	code	count(code)
0	LCY	51
1	LGW	232
2	LHR	221
3	LTN	130
4	STN	211
We need to specify the region, because there is another city called London, not in the UK.

How many airports are reachable from London, UK in two hops?

lon_uk_airports[code] := *airport{code, city: 'London', region: 'GB-ENG'}
one_hop[to] := lon_uk_airports[fr], *route{fr, to}, not lon_uk_airports[to];
?[count_unique(a3)] := one_hop[a2], *route{fr: a2, to: a3}, not lon_uk_airports[a3];
 	count_unique(a3)
0	2353
What are the cities directly reachable from LGW (London Gatwick), but furthermost away?

?[city, dist] := *route{fr: 'LGW', to, dist},
                 *airport{code: to, city}
:order -dist
:limit 10
 	city	dist
0	Buenos Aires	6908.000000
1	Singapore	6751.000000
2	Langkawi	6299.000000
3	Duong Dong	6264.000000
4	Taipei	6080.000000
5	Port Louis	6053.000000
6	Rayong	6008.000000
7	Cape Town	5987.000000
8	Hong Kong	5982.000000
9	Shanghai	5745.000000
What airports are within 0.1 degrees of the Greenwich meridian?

?[code, desc, lon, lat] := *airport{lon, lat, code, desc}, lon > -0.1, lon < 0.1
 	code	desc	lon	lat
0	CDT	Castellon De La Plana Airport	0.026111	39.999199
1	LCY	London City Airport	0.055278	51.505278
2	LDE	Tarbes-Lourdes-Pyrénées Airport	-0.006439	43.178699
3	LEH	Le Havre Octeville Airport	0.088056	49.533901
Airports in a box drawn around London Heathrow, UK:

h_box[lon, lat] := *airport{code: 'LHR', lon, lat}
?[code, desc] := h_box[lhr_lon, lhr_lat], *airport{code, lon, lat, desc},
                 abs(lhr_lon - lon) < 1, abs(lhr_lat - lat) < 1
 	code	desc
0	LCY	London City Airport
1	LGW	London Gatwick
2	LHR	London Heathrow
3	LTN	London Luton Airport
4	SOU	Southampton Airport
5	STN	London Stansted Airport
For some spherical geometry: what is the angle subtended by SFO and NRT on the surface of the earth?

?[deg_diff] := *airport{code: 'SFO', lat: a_lat, lon: a_lon},
               *airport{code: 'NRT', lat: b_lat, lon: b_lon},
               deg_diff = rad_to_deg(haversine_deg_input(a_lat, a_lon, b_lat, b_lon))
 	deg_diff
0	73.992112
We mentioned before that aggregations in Cozo are powerful. They are powerful because they can be used in recursions (some restrictions apply).

Let’s find the distance of the shortest route between two airports. One wayis to enumerate all the routes between the two airports, and then apply min aggregation to the results. This cannot be implemented as stated, since the routes may contain cycles and hence there can be an infinite number of routes between two airports.

Instead, think recursively. If we already have all the shortest routes between all nodes, we derive an equation satisfied by the shortest route: the shortest route between a and b is either the distance of a direct route, or the sum of the shortest distance from a to c and the distance of a direct route from c to d. We apply our min aggregation to this recursive set instead.

Write it out and it works. For exmaple, the shortest routes between the airports LHR and YPO:

shortest[b, min(dist)] := *route{fr: 'LHR', to: b, dist}
                          # Start with the airport 'LHR', retrieve a direct route from 'LHR' to b

shortest[b, min(dist)] := shortest[c, d1], # Start with an existing shortest route from 'LHR' to c
                          *route{fr: c, to: b, dist: d2},  # Retrieve a direct route from c to b
                          dist = d1 + d2 # Add the distances

?[dist] := shortest['YPO', dist] # Extract the answer for 'YPO'.
                                 # We chose it since it is the hardest airport to get to from 'LHR'.
 	dist
0	4147.000000
There is a caveat when you try to write similar queries. Say you try to write it in the following way (don’t try to run it):

shortest[a, b, min(dist)] := *route{fr: a, to: b, dist}
shortest[a, b, min(dist)] := shortest[a, c, d1],
                          *route{fr: c, to: b, dist: d2},
                          dist = d1 + d2

?[dist] := shortest['LHR', 'YPO', dist]
You will find that the query does not complete in a reasonable amount of time, despite it being equivalent to the original query. Why?

In the changed query, you are asking the database to compute the all-pair shortest path, and then extract the answer to a particular shortest path. Normally Cozo would apply a technique called magic set rewrite so that only the needed answer would be calculated. However, in the changed query the presence of the aggregation operator min prevents that. In this case, applying the rewrite to the variable a would still yield the correct answer, but rewriting in any other way would give complete nonsense, and in the more general case with recursive aggregations this is a can of worms.

So as explained in the chapter about execution, magic set rewrites are only applied to rules without aggregations or recursions for the moment, until we are sure of the exact conditions under which the rewrites are safe. So for now at least the database executes the query as written, computing the result of the shortest rule containing more than ten million rows (to be exact, 3700 * 3700 = 13,690,000 rows) first!

The bottom line is, be mindful of the cardinality of the return sets of recursive rules.

A tour of graph algorithms
Now let’s investigate the graph using some graph algorithms. As we have mentioned before, the Cozo running in browsers through WASM does not have the graph algorithms module enabled, so to run the following examples you will need to use some other implementation (for example, the Python one).

Since path-finding is such a common operation on graphs, Cozo has several fixed rules for that:

starting[] <- [['LHR']]
goal[] <- [['YPO']]
?[starting, goal, distance, path] <~ ShortestPathDijkstra(*route[], starting[], goal[])
 	starting	goal	distance	path
0	LHR	YPO	4147.000000	['LHR', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
Not only is it more efficient, but we also get a path for the shortest route.

Not content with the shortest path, the following calculates ten the shortest paths:

starting[] <- [['LHR']]
goal[] <- [['YPO']]
?[starting, goal, distance, path] <~ KShortestPathYen(*route[], starting[], goal[], k: 10)
 	starting	goal	distance	path
0	LHR	YPO	4147.000000	['LHR', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
1	LHR	YPO	4150.000000	['LHR', 'DUB', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
2	LHR	YPO	4164.000000	['LHR', 'YUL', 'YMT', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
3	LHR	YPO	4167.000000	['LHR', 'DUB', 'YUL', 'YMT', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
4	LHR	YPO	4187.000000	['LHR', 'MAN', 'DUB', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
5	LHR	YPO	4202.000000	['LHR', 'IOM', 'DUB', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
6	LHR	YPO	4204.000000	['LHR', 'MAN', 'DUB', 'YUL', 'YMT', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
7	LHR	YPO	4209.000000	['LHR', 'YUL', 'YMT', 'YNS', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
8	LHR	YPO	4211.000000	['LHR', 'MAN', 'IOM', 'DUB', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
9	LHR	YPO	4212.000000	['LHR', 'DUB', 'YUL', 'YMT', 'YNS', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
If efficiency is really important to you, you can use the A* algorithm with a good heuristic function:

code_lat_lon[code, lat, lon] := *airport{code, lat, lon}
starting[code, lat, lon] := code = 'LHR', *airport{code, lat, lon};
goal[code, lat, lon] := code = 'YPO', *airport{code, lat, lon};
?[] <~ ShortestPathAStar(*route[],
                         code_lat_lon[node, lat1, lon1],
                         starting[],
                         goal[goal, lat2, lon2],
                         heuristic: haversine_deg_input(lat1, lon1, lat2, lon2) * 3963);
 	_0	_1	_2	_3
0	LHR	YPO	4147.000000	['LHR', 'YUL', 'YVO', 'YKQ', 'YMO', 'YFA', 'ZKE', 'YAT', 'YPO']
There’s a lot more setup required in this case: we need to retrieve the latitudes and longitudes of airports and do processing on them first. The number 3963 above is the radius of the earth in miles.

The most important airports, by PageRank:

rank[code, score] <~ PageRank(*route[a, b])
?[code, desc, score] := rank[code, score], *airport{code, desc}

:limit 10;
:order -score
 	code	desc	score
0	IST	Istanbul International Airport	0.004889
1	DFW	Dallas/Fort Worth International Airport	0.004696
2	ORD	Chicago O'Hare International Airport	0.004452
3	DEN	Denver International Airport	0.004252
4	PEK	Beijing Capital International Airport	0.004044
5	FRA	Frankfurt am Main	0.004027
6	ATL	Hartsfield - Jackson Atlanta International Airport	0.004022
7	DXB	Dubai International Airport	0.004002
8	CDG	Paris Charles de Gaulle	0.003998
9	DME	Moscow, Domodedovo International Airport	0.003817
The following example takes a long time to run since it calculates the betweenness centrality: up to a few seconds, depending on your machine. Algorithms for calculating the betweenness centrality have high complexity.

centrality[code, score] <~ BetweennessCentrality(*route[a, b])
?[code, desc, score] := centrality[code, score], *airport{code, desc}

:limit 10;
:order -score
 	code	desc	score
0	ANC	Anchorage Ted Stevens	1074868.250000
1	KEF	Reykjavik, Keflavik International Airport	928450.437500
2	HEL	Helsinki Ventaa	581588.500000
3	PEK	Beijing Capital International Airport	532021.062500
4	DEL	Indira Gandhi International Airport	472979.968750
5	IST	Istanbul International Airport	457882.156250
6	PKC	Yelizovo Airport	408571.000000
7	MSP	Minneapolis-St.Paul International Airport	396433.250000
8	LAX	Los Angeles International Airport	393309.968750
9	DEN	Denver International Airport	374339.531250
These are the airports that, if disconnected from the network, cause the most disruption. As this example shows, some of the algorithms really struggle when you go beyond small or medium sized dataset.

Community detection can collapse a graph into a supergraph. Here we store the result, since it has too many rows to display nicely:

community[detailed_cluster, code] <~ CommunityDetectionLouvain(*route[a, b])
?[code, cluster, detailed_cluster] := community[detailed_cluster, code], cluster = first(detailed_cluster)

:replace community {code => cluster, detailed_cluster}
 	status
0	OK
We can look at the supernodes containing specific nodes. For example, the supernode for London Gatwick consists of mainly UK and other European airports, as you would expect:

community[code] := *community{code: 'LGW', cluster}, *community{code, cluster}
?[country, count(code)] :=
    community[code],
    *airport{code, desc, country: country_code},
    *country{code: country_code, desc: country},

:order -count(code)
:limit 5
 	country	count(code)
0	United Kingdom	54
1	France	50
2	Norway	49
3	Spain	40
4	Greece	38
For JFK on the other hand, its supernode consists of mainly US airports:

community[code] := *community{code: 'JFK', cluster}, *community{code, cluster}
?[country, count(code)] :=
    community[code],
    *airport{code, desc, country: country_code},
    *country{code: country_code, desc: country},

:order -count(code)
:limit 5
 	country	count(code)
0	United States	444
1	Canada	111
2	Brazil	108
3	Mexico	57
4	Colombia	50
But it does not always work according to geography. For example, Frankfurt airport is in Germany:

?[desc, country_desc] := *airport{code: 'FRA', desc, country: country_code}, *country{code: country_code, desc: country_desc}
 	desc	country_desc
0	Frankfurt am Main	Germany
But its supernode:

community[code] := *community{code: 'FRA', cluster}, *community{code, cluster}
?[country, count(code)] :=
    community[code],
    *airport{code, desc, country: country_code},
    *country{code: country_code, desc: country},

:order -count(code)
:limit 5
 	country	count(code)
0	United States	444
1	Canada	111
2	Brazil	108
3	Mexico	57
4	Colombia	50
Germany does not even appear in the top five. In fact, FRA is in the same supernode as JFK. What matters is the connectivity in the graph, not the geography. As another example:

community[code] := *community{code: 'SIN', cluster}, *community{code, cluster}
?[country, count(code)] :=
    community[code],
    *airport{code, desc, country: country_code},
    *country{code: country_code, desc: country},

:order -count(code)
:limit 5
 	country	count(code)
0	China	216
1	Australia	125
2	Indonesia	68
3	Japan	65
4	Philippines	40
You’d expect SIN to be a Chinese airport. Wrong:

?[desc, country_desc] := *airport{code: 'SIN', desc, country: country_code}, *country{code: country_code, desc: country_desc}
 	desc	country_desc
0	Singapore, Changi International Airport	Singapore
Finally, let’s collapse the route relation into super_route:

?[fr_cluster, to_cluster, count(dist), sum(dist)] := *route{fr, to, dist},
                                                     *community{code: fr, cluster: fr_cluster},
                                                     *community{code: to, cluster: to_cluster}
:replace super_route {fr_cluster, to_cluster => n_routes=count(dist), total_distance=sum(dist)}
 	status
0	OK
As expected, the “diagonals” where fr_cluster == to_cluster are larger in the super_route graph:

?[fr_cluster, to_cluster, n_routes, total_distance] := *super_route{fr_cluster, to_cluster, n_routes, total_distance}, fr_cluster < 2
 	fr_cluster	to_cluster	n_routes	total_distance
0	0	0	9041	8933554.000000
1	0	1	434	1695379.000000
2	0	2	228	761661.000000
3	0	3	530	1681865.000000
4	0	4	163	391892.000000
5	0	8	3	300.000000
6	0	11	2	283.000000
7	0	19	1	238.000000
8	0	21	2	705.000000
9	0	22	1	975.000000
10	1	0	434	1696858.000000
11	1	1	4474	5142452.000000
12	1	2	1160	1492734.000000
13	1	3	526	1724591.000000
14	1	4	223	361986.000000
15	1	9	1	808.000000
Now the super graph is small enough that all analytics algorithms return instantly:

?[cluster, score] <~ PageRank(*super_route[])
:order -score
:limit 5
 	cluster	score
0	3	0.173309
1	0	0.093072
2	1	0.053465
3	2	0.053389
4	4	0.044654
You can now go on to investigate the supernodes, give real-world interpretations to them, etc. For example, a naïve interpretation of the above PageRank result is that North America is (still) the most prosperous part of the world, followed by East Asia in the second place, South Asia in the third place, and Europe in the fourth place.

Importing dataset the hard way
Previously, we imported the air-routes dataset by using Python under the hood to download a specially-crafted JSON file and feed it to the database. Here we learn how to achieve the same effect by letting Cozo fetch and import a series of CSV files, without Python’s help.

Let’s set the database magic up first:

::access_level normal airport, contain, continent, country, route
 	status
0	OK
::remove airport, contain, continent, country, route, community, super_route
 	status
0	OK
Next, some parameters to make life eaiser (the lines commented out do the same thing by processing local files):

# %cozo_set AIR_ROUTES_NODES_URL 'https://raw.githubusercontent.com/cozodb/cozo/dev/cozo-core/tests/air-routes-latest-nodes.csv'
# %cozo_set AIR_ROUTES_EDGES_URL 'https://raw.githubusercontent.com/cozodb/cozo/dev/cozo-core/tests/air-routes-latest-edges.csv'
%cozo_set AIR_ROUTES_NODES_URL 'file://./../../cozo/cozo-core/tests/air-routes-latest-nodes.csv'
%cozo_set AIR_ROUTES_EDGES_URL 'file://./../../cozo/cozo-core/tests/air-routes-latest-edges.csv'
First, import the airport relation:

res[idx, label, typ, code, icao, desc, region, runways, longest, elev, country, city, lat, lon] <~
    CsvReader(types: ['Int', 'Any', 'Any', 'Any', 'Any', 'Any', 'Any', 'Int?', 'Float?', 'Float?', 'Any', 'Any', 'Float?', 'Float?'],
              url: $AIR_ROUTES_NODES_URL,
              has_headers: true)

?[code, icao, desc, region, runways, longest, elev, country, city, lat, lon] :=
    res[idx, label, typ, code, icao, desc, region, runways, longest, elev, country, city, lat, lon],
    label == 'airport'

:replace airport {
    code: String
    =>
    icao: String,
    desc: String,
    region: String,
    runways: Int,
    longest: Float,
    elev: Float,
    country: String,
    city: String,
    lat: Float,
    lon: Float
}
 	status
0	OK
The CsvReader utility downloads a CSV file from the internet and attempts to parse its content into a relation. When we store the relation, we specified types for the columns. The code column acts as a primary key for the airport stored relation.

Next is country:

res[idx, label, typ, code, icao, desc] <~
    CsvReader(types: ['Int', 'Any', 'Any', 'Any', 'Any', 'Any'],
              url: $AIR_ROUTES_NODES_URL,
              has_headers: true)
?[code, desc] :=
    res[idx, label, typ, code, icao, desc],
    label == 'country'

:replace country {
    code: String
    =>
    desc: String
}
 	status
0	OK
continent:

res[idx, label, typ, code, icao, desc] <~
    CsvReader(types: ['Int', 'Any', 'Any', 'Any', 'Any', 'Any'],
              url: $AIR_ROUTES_NODES_URL,
              has_headers: true)
?[idx, code, desc] :=
    res[idx, label, typ, code, icao, desc],
    label == 'continent'

:replace continent {
    code: String
    =>
    desc: String
}
 	status
0	OK
We need to make a translation table for the indices the data use:

res[idx, label, typ, code] <~
    CsvReader(types: ['Int', 'Any', 'Any', 'Any'],
              url: $AIR_ROUTES_NODES_URL,
              has_headers: true)
?[idx, code] :=
    res[idx, label, typ, code],

:replace idx2code { idx => code }
 	status
0	OK
The contain relation contains information on the geographical inclusion of entities:

res[] <~
    CsvReader(types: ['Int', 'Int', 'Int', 'String'],
              url: $AIR_ROUTES_EDGES_URL,
              has_headers: true)
?[entity, contained] :=
    res[idx, fr_i, to_i, typ],
    typ == 'contains',
    *idx2code[fr_i, entity],
    *idx2code[to_i, contained]


:replace contain { entity: String, contained: String }
 	status
0	OK
Finally, the routes between the airports. This relation is much larger than the rest and contains about 60k rows:

res[] <~
    CsvReader(types: ['Int', 'Int', 'Int', 'String', 'Float?'],
              url: $AIR_ROUTES_EDGES_URL,
              has_headers: true)
?[fr, to, dist] :=
    res[idx, fr_i, to_i, typ, dist],
    typ == 'route',
    *idx2code[fr_i, fr],
    *idx2code[to_i, to]

:replace route { fr: String, to: String => dist: Float }
 	status
0	OK
We no longer need the idx2code relation:

::remove idx2code
 	status
0	OK
Let’s verify all the relations we want are there:

::relations
 	name	arity	access_level	n_keys	n_non_keys	n_put_triggers	n_rm_triggers	n_replace_triggers	description
0	airport	11	normal	1	10	0	0	0	
1	contain	2	normal	2	0	0	0	0	
2	continent	2	normal	1	1	0	0	0	
3	country	2	normal	1	1	0	0	0	
4	dept_info	4	normal	2	2	0	0	0	
5	route	3	normal	2	1	0	0	0	
6	test	1	normal	1	0	0	0	0	
7	test2	1	normal	1	0	0	0	0	
