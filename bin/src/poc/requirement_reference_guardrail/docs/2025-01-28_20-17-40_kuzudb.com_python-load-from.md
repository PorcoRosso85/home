# Python API

Kuzu provides a Python package that you can install via PyPI. A full list of the available functions and classes
can be found in the Python API documentation, linked below.

[Python API source documentation](https://kuzudb.com/api-docs/python)

## Sync and Async APIs

Kuzu provides both a synchronous and an asynchronous Python API. The synchronous API is the default
and is more convenient to use.

Download the [CSV files](https://github.com/kuzudb/kuzu/tree/master/dataset/demo-db/csv) used in the examples below:

Terminal window ```
mkdir ./data/curl -L -o ./data/city.csv https://raw.githubusercontent.com/kuzudb/kuzu/refs/heads/master/dataset/demo-db/csv/city.csvcurl -L -o ./data/user.csv https://raw.githubusercontent.com/kuzudb/kuzu/refs/heads/master/dataset/demo-db/csv/user.csvcurl -L -o ./data/follows.csv https://raw.githubusercontent.com/kuzudb/kuzu/refs/heads/master/dataset/demo-db/csv/follows.csvcurl -L -o ./data/lives-in.csv https://raw.githubusercontent.com/kuzudb/kuzu/refs/heads/master/dataset/demo-db/csv/lives-in.csv
```

- [Sync API](#tab-panel-14)
- [Async API](#tab-panel-15)

The synchronous API is the default and is a common way to work with Kuzu in Python.

```
import kuzu
def main() -> None:    # Create an empty on-disk database and connect to it    db = kuzu.Database("example.kuzu")    conn = kuzu.Connection(db)
    create_tables(conn)    copy_data(conn)    query(conn)
def create_tables(conn: kuzu.Connection) -> None:    conn.execute("CREATE NODE TABLE User(name STRING PRIMARY KEY, age INT64)")    conn.execute("CREATE NODE TABLE City(name STRING PRIMARY KEY, population INT64)")    conn.execute("CREATE REL TABLE Follows(FROM User TO User, since INT64)")    conn.execute("CREATE REL TABLE LivesIn(FROM User TO City)")
def copy_data(conn: kuzu.Connection) -> None:    conn.execute('COPY User FROM "./data/user.csv"')    conn.execute('COPY City FROM "./data/city.csv"')    conn.execute('COPY Follows FROM "./data/follows.csv"')    conn.execute('COPY LivesIn FROM "./data/lives-in.csv"')
def query(conn: kuzu.Connection) -> None:    results = conn.execute("""        MATCH (a:User)-[f:Follows]->(b:User)        RETURN a.name, b.name, f.since;    """)    for row in results:        print(row)
if __name__ == "__main__":    main()
```

The asynchronous API is useful for running Kuzu in an async context,
such as in web frameworks like FastAPI or cases where you need to concurrently run queries in Kuzu.

```
import asyncioimport kuzu
async def main():    # Create an empty on-disk database and connect to it    db = kuzu.Database("example.kuzu")    # The underlying connection pool will be automatically created and managed by the async connection    conn = kuzu.AsyncConnection(db, max_concurrent_queries=4)
    await create_tables(conn)    await copy_data(conn)    await query(conn)
async def create_tables(conn: kuzu.AsyncConnection) -> None:    await conn.execute("CREATE NODE TABLE User(name STRING PRIMARY KEY, age INT64)")    await conn.execute(        "CREATE NODE TABLE City(name STRING PRIMARY KEY, population INT64)"    )    await conn.execute("CREATE REL TABLE Follows(FROM User TO User, since INT64)")    await conn.execute("CREATE REL TABLE LivesIn(FROM User TO City)")
async def copy_data(conn: kuzu.AsyncConnection) -> None:    await conn.execute("COPY User FROM './data/user.csv'")    await conn.execute("COPY City FROM './data/city.csv'")    await conn.execute("COPY Follows FROM './data/follows.csv'")    await conn.execute("COPY LivesIn FROM './data/lives-in.csv'")
async def query(conn: kuzu.AsyncConnection) -> None:    results = await conn.execute("""        MATCH (a:User)-[f:Follows]->(b:User)        RETURN a.name, b.name, f.since;    """)    for row in results:        print(row)
if __name__ == "__main__":    asyncio.run(main())
```

The async API in Python is backed by a thread pool. The thread pool is automatically
created and managed by the async connection. You can configure the number of concurrent
queries by setting the `max_concurrent_queries` parameter, as shown above.

## Output utilities

The Python API provides some utilities to process query results.

```
# Get all rows as a list of tuplesprint(response.get_all())
# Change the output format to a dictionary, where the keys are the column namesprint(response.rows_as_dict().get_all())
# Get the first 2 rows as a list of tuplesprint(response.get_n(2))
# Get the next row as a tupleif response.has_next():    print(response.get_next())
# Get all rows as a list of tuplesprint(list(response))
```

## Run multiple queries in one execution

By default, executing a single query in the Python API will return a `QueryResult` object. However,
if you submit multiple Cypher queries separated by semicolons in a single execution, the API will
return a list of `QueryResult` objects.

You can loop through each result of a `QueryResult` object and get its contents.

```
responses = conn.execute("""    RETURN 42;    RETURN 'Alice', 'Bob', 'Charlie';    RETURN [true, false], 3.14;""")for response in responses:    for row in response:        print(row)
```

```
[42]['Alice', 'Bob', 'Charlie'][[True, False], 3.14]
```

## DataFrames and Arrow Tables

In Python, Kuzu supports the use of Pandas and Polars DataFrames, as well as PyArrow Tables. This
allows you to leverage the data manipulation capabilities of these libraries in your graph workflows.

### Output query results

You can output the results of a Cypher query to a Pandas DataFrame, Polars DataFrame, or PyArrow Table.
The following examples show how to output query results to each of these data structures.

- [Pandas](#tab-panel-16)
- [Polars](#tab-panel-17)
- [Arrow Table](#tab-panel-18)

You can output the results of a Cypher query to a Pandas DataFrame using the `get_as_df()` method:

```
import kuzuimport pandas as pd
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
conn.execute("CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)")conn.execute("CREATE (a:Person {name: 'Adam', age: 30})")conn.execute("CREATE (a:Person {name: 'Karissa', age: 40})")conn.execute("CREATE (a:Person {name: 'Zhang', age: 50})")
result = conn.execute("MATCH (p:Person) RETURN p.*")print(result.get_as_df())
```

```
    p.name  p.age0     Adam     301  Karissa     402    Zhang     50
```

Return specific columns by name and optionally alias them as follows:

```
result = conn.execute("MATCH (p:Person) RETURN p.name AS name")print(result.get_as_df())
```

```
      name0     Adam1  Karissa2    Zhang
```

You can output the results of a Cypher query to a Polars DataFrame using the `get_as_pl()` method:

```
import kuzuimport polars as pl
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
conn.execute("CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)")conn.execute("CREATE (a:Person {name: 'Adam', age: 30})")conn.execute("CREATE (a:Person {name: 'Karissa', age: 40})")conn.execute("CREATE (a:Person {name: 'Zhang', age: 50})")
result = conn.execute("MATCH (p:Person) RETURN p.*")print(result.get_as_pl())
```

```
shape: (3, 2)┌─────────┬───────┐│ p.name  ┆ p.age ││ ---     ┆ ---   ││ str     ┆ i64   │╞═════════╪═══════╡│ Adam    ┆ 30    ││ Karissa ┆ 40    ││ Zhang   ┆ 50    │└─────────┴───────┘
```

Return specific columns by name and optionally alias them as follows:

```
result = conn.execute("MATCH (p:Person) RETURN p.name AS name")print(result.get_as_pl())
```

```
shape: (3, 1)┌─────────┐│ name    ││ ---     ││ str     │╞═════════╡│ Adam    ││ Karissa ││ Zhang   │└─────────┘
```

You can output the results of a Cypher query to a PyArrow Table using the `get_as_arrow()` method:

```
import kuzuimport pyarrow as pa
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
conn.execute("CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)")conn.execute("CREATE (a:Person {name: 'Adam', age: 30})")conn.execute("CREATE (a:Person {name: 'Karissa', age: 40})")conn.execute("CREATE (a:Person {name: 'Zhang', age: 50})")
result = conn.execute("MATCH (p:Person) RETURN p.*")print(result.get_as_arrow())
```

```
pyarrow.Tablep.name: stringp.age: int64----p.name: [["Adam","Karissa","Zhang"]]p.age: [[30,40,50]]
```

You can scan a Pandas DataFrame, Polars DataFrame, or PyArrow Table in Kuzu using the `LOAD FROM` clause.
Scanning a DataFrame or Table does *not* copy the data into Kuzu, it only reads the data.

- [Pandas](#tab-panel-19)
- [Polars](#tab-panel-20)
- [Arrow Table](#tab-panel-21)

```
import kuzuimport pandas as pd
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
df = pd.DataFrame({    "name": ["Adam", "Karissa", "Zhang"],    "age": [30, 40, 50]})
result = conn.execute("LOAD FROM df RETURN *")print(result.get_as_df())
```

```
      name  age0     Adam   301  Karissa   402    Zhang   50
```

```
import kuzuimport polars as pl
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
df = pl.DataFrame({    "name": ["Adam", "Karissa", "Zhang"],    "age": [30, 40, 50]})
result = conn.execute("LOAD FROM df RETURN *")print(result.get_as_pl())
```

```
shape: (3, 2)┌─────────┬─────┐│ name    ┆ age ││ ---     ┆ --- ││ str     ┆ i64 │╞═════════╪═════╡│ Adam    ┆ 30  ││ Karissa ┆ 40  ││ Zhang   ┆ 50  │└─────────┴─────┘
```

```
import kuzuimport pyarrow as pa
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
tbl = pa.table({    "name": ["Adam", "Karissa", "Zhang"],    "age": [30, 40, 50]})
result = conn.execute("LOAD FROM tbl RETURN *")print(result.get_as_arrow())
```

```
pyarrow.Tablename: stringage: int64----name: [["Adam","Karissa","Zhang"]]age: [[30,40,50]]
```

### COPY FROM

- [Pandas](#tab-panel-22)
- [Polars](#tab-panel-23)
- [Arrow Table](#tab-panel-24)

Copy from a Pandas DataFrame into a Kuzu table using the `COPY FROM` command:

```
import kuzuimport pandas as pd
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
conn.execute("CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)")
df = pd.DataFrame({    "name": ["Adam", "Karissa", "Zhang"],    "age": [30, 40, 50]})
conn.execute("COPY Person FROM df")
result = conn.execute("MATCH (p:Person) RETURN p.*")print(result.get_as_df())
```

```
    p.name  p.age0     Adam     301  Karissa     402    Zhang     50
```

Copy from a Polars DataFrame into a Kuzu table using the `COPY FROM` command:

```
import kuzuimport polars as pl
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
conn.execute("CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)")
df = pl.DataFrame({    "name": ["Adam", "Karissa", "Zhang"],    "age": [30, 40, 50]})
conn.execute("COPY Person FROM df")
result = conn.execute("MATCH (p:Person) RETURN p.*")print(result.get_as_pl())
```

```
shape: (3, 2)┌─────────┬───────┐│ p.name  ┆ p.age ││ ---     ┆ ---   ││ str     ┆ i64   │╞═════════╪═══════╡│ Adam    ┆ 30    ││ Karissa ┆ 40    ││ Zhang   ┆ 50    │└─────────┴───────┘
```

Copy from a PyArrow Table into a Kuzu table using the `COPY FROM` command:

```
import kuzuimport pyarrow as pa
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
conn.execute("CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)")
tbl = pa.table({    "name": ["Adam", "Karissa", "Zhang"],    "age": [30, 40, 50]})
conn.execute("COPY Person FROM tbl")
result = conn.execute("MATCH (p:Person) RETURN p.*")print(result.get_as_arrow())
```

```
pyarrow.Tablep.name: stringp.age: int64----p.name: [["Adam","Karissa","Zhang"]]p.age: [[30,40,50]]
```

---

## Type notation

This section summarizes the type notation used in Kuzu’s Python API. Below is a table from Python
types to a Kuzu `LogicalTypeID`, which will be used to infer types via Python type annotations.

| Python type | Kuzu `LogicalTypeID` |
| --- | --- |
| `bool` | `BOOL` |
| `int` | `INT64` |
| `float` | `DOUBLE` |
| `str` | `STRING` |
| `datetime` | `TIMESTAMP` |
| `date` | `DATE` |
| `timedelta` | `INTERVAL` |
| `uuid` | `UUID` |
| `list` | `LIST` |
| `dict` | `MAP` |

## UDF

Kuzu’s Python API also supports the registration of User Defined Functions (UDFs),
allowing you to define custom functions in Python and use them in your Cypher queries. This can allow
you to quickly extend Kuzu with new functions you need in your Python applications.

An example of using the UDF API is shown below. We will define a Python UDF that calculates the
difference between two numbers, and then apply it in a Cypher query.

### Register the UDF

```
import kuzu
db = kuzu.Database(":memory:")conn = kuzu.Connection(db)
# define your functiondef difference(a, b):    return a - b
# define the expected type of your parametersparameters = [kuzu.Type.INT64, kuzu.Type.INT64]
# define expected type of the returned valuereturn_type = kuzu.Type.INT64
# register the UDFconn.create_function("difference", difference, parameters, return_type)
```

Note that in the example above, we explicitly declared the expected types of the parameters and the
return value in Kuzu, prior to registering the UDF.

Alternatively, you can simply use Python type annotations to denote the type signature of the
parameters and return value.

```
def difference(a : int, b : int) -> int:    return abs(a - b)
conn.create_function("difference", difference)
```

#### Additional parameters

The UDF API’s `create_function` provides the following additional parameters:

- `name: str` : The name of the function to be invoked in cypher.
- `udf: Callable[[...], Any]` : The function to be executed.
- `params_type: Optional[list[Type | str]]` : A list whose elements can either be `kuzu.Type` or `str`. `kuzu.Type`
can be used to denote nonnested parameter types, while `str` can be used to denote both nested and nonnested parameter types.
Details on how to denote types are in the [type notation](#type-notation) section.
- `return_type: Optional[Type | str]` : Either a `kuzu.Type` enum or `str`. Details on how to denote types are in the [type notation](#type-notation) section.
- `default_null_handling: Optional[bool]` : True by default. When true, if any one of the inputs is null, function execution is skipped and the output is resolved to null.
- `catch_exceptions: Optional[bool]` : False by default. When true, if the UDF raises an exception, the output is resolved to null. Otherwise the Exception is rethrown.

### Apply the UDF

Once the UDF is registered, you can apply it in a Cypher query. First, let’s create some data.

```
conn.execute("CREATE NODE TABLE IF NOT EXISTS Item (id INT64 PRIMARY KEY, a INT64, b INT64, c INT64)")
conn.execute("CREATE (i:Item {id: 1}) SET i.a = 134, i.b = 123")conn.execute("CREATE (i:Item {id: 2}) SET i.a = 44, i.b = 29")conn.execute("CREATE (i:Item {id: 3}) SET i.a = 32, i.b = 68")
```

We’re now ready to apply the UDF in a Cypher query:

```
result = conn.execute("MATCH (i:Item) RETURN i.a AS a, i.b AS b, difference (i.a, i.b) AS difference")print(result.get_as_df())
```

The output should be:

```
     a    b  difference0  134  123          111   44   29          152   32   68         -36
```

### Remove UDF

In case you want to remove the UDF, you can call the `remove_function` method on the connection object.

```
conn.remove_function("difference")
```

### Nested and complex types

When working with UDFs, you can also specify nested or complex types, though in this case, there are some differences
from the examples shown above. With these additional types, a string representation should be given
for the parameters which are then manually casted to the respective Kuzu type.

Some examples of where this is relevant are listed below:

- A list of `INT64` would be `"INT64[]"`
- A map from a `STRING` to a `DOUBLE` would be `"MAP(STRING, DOUBLE)"`
- A Decimal value with 7 significant figures and 2 decimals would be `"DECIMAL(7, 2)"`

Note that it’s also valid to define child types through Python’s type annotations, e.g. `list[int]`,
or `dict(str, float)` for simple types.

Below, we show an example to calculate the discounted price of an item using a Python UDF.

```
def calculate_discounted_price(price: float, has_discount: bool) -> float:    # Assume 10% discount on all items for simplicity    return float(price) * 0.9 if has_discount else price
parameters = ['DECIMAL(7, 2)', kuzu.Type.BOOL]
return_type = 'DECIMAL(7, 2)'
conn.create_function(    "current_price",    calculate_discounted_price,    parameters,    return_type)
result = conn.execute(    """    RETURN        current_price(100, true) AS discount,        current_price(100, false) AS no_discount;    """)print(result.get_as_df())
```

```
  discount no_discount0    90.00      100.00
```

The second parameter is a built-in native type in Kuzu, i.e., `kuzu.Type.BOOL`. For the first parameter,
we need to specify a string, i.e. `DECIMAL(7,2)` that is then parsed and used by Kuzu
to map to the internal decimal representation.
