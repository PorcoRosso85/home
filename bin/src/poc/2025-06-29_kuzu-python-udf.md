---
url: https://docs.kuzudb.com/client-apis/python/#udf
saved_at: 2025-06-29T12:00:00Z
title: KuzuDB Python UDF Documentation
---

# UDF

Kuzu's Python API also supports the registration of User Defined Functions (UDFs),
allowing you to define custom functions in Python and use them in your Cypher queries. This can allow
you to quickly extend Kuzu with new functions you need in your Python applications.

An example of using the UDF API is shown below. We will define a Python UDF that calculates the
difference between two numbers, and then apply it in a Cypher query.

## Register the UDF

```python
import kuzu

db = kuzu.Database("test_db")
conn = kuzu.Connection(db)

# define your function
def difference(a, b):
    return a - b

# define the expected type of your parameters
parameters = [kuzu.Type.INT64, kuzu.Type.INT64]

# define expected type of the returned value
return_type = kuzu.Type.INT64

# register the UDF
conn.create_function("difference", difference, parameters, return_type)
```

Note that in the example above, we explicitly declared the expected types of the parameters and the
return value in Kuzu, prior to registering the UDF.

Alternatively, you can simply use Python type annotations to denote the type signature of the
parameters and return value.

```python
def difference(a : int, b : int) -> int:
    return abs(a - b)

conn.create_function("difference", difference)
```

### Additional parameters

The UDF API's `create_function` provides the following additional parameters:

- `name: str` : The name of the function to be invoked in cypher.
- `udf: Callable[[...], Any]` : The function to be executed.
- `params_type: Optional[list[Type | str]]` : A list whose elements can either be `kuzu.Type` or `str`. `kuzu.Type`
can be used to denote nonnested parameter types, while `str` can be used to denote both nested and nonnested parameter types.
Details on how to denote types are in the [type notation](#type-notation) section.
- `return_type: Optional[Type | str]` : Either a `kuzu.Type` enum or `str`. Details on how to denote types are in the [type notation](#type-notation) section.
- `default_null_handling: Optional[bool]` : True by default. When true, if any one of the inputs is null, function execution is skipped and the output is resolved to null.
- `catch_exceptions: Optional[bool]` : False by default. When true, if the UDF raises an exception, the output is resolved to null. Otherwise the Exception is rethrown.

## Apply the UDF

Once the UDF is registered, you can apply it in a Cypher query. First, let's create some data.

```python
# create a table
conn.execute("CREATE NODE TABLE IF NOT EXISTS Item (id INT64, a INT64, b INT64, c INT64, PRIMARY KEY(id))")

# insert some data
conn.execute("CREATE (i:Item {id: 1}) SET i.a = 134, i.b = 123")
conn.execute("CREATE (i:Item {id: 2}) SET i.a = 44, i.b = 29")
conn.execute("CREATE (i:Item {id: 3}) SET i.a = 32, i.b = 68")
```

We're now ready to apply the UDF in a Cypher query:

```python
# apply the UDF and print the results
result = conn.execute("MATCH (i:Item) RETURN i.a AS a, i.b AS b, difference (i.a, i.b) AS difference")
print(result.get_as_df())
```

The output should be:

```
     a    b  difference
0  134  123          11
1   44   29          15
2   32   68         -36
```

## Remove UDF

In case you want to remove the UDF, you can call the `remove_function` method on the connection object.

```python
# Use existing connection object
conn.remove_function(difference)
```

## Nested and complex types

When working with UDFs, you can also specify nested or complex types, though in this case, there are some differences
from the examples shown above. With these additional types, a string representation should be given
for the parameters which are then manually casted to the respective Kuzu type.

Some examples of where this is relevant are listed below:

- A list of `INT64` would be `"INT64[]"`
- A map from a `STRING` to a `DOUBLE` would be `"MAP(STRING, DOUBLE)"`
- A Decimal value with 7 significant figures and 2 decimals would be `"DECIMAL(7, 2)"`

Note that it's also valid to define child types through Python's type annotations, e.g. `list[int]`,
or `dict(str, float)` for simple types.

Below, we show an example to calculate the discounted price of an item using a Python UDF.

```python
def calculate_discounted_price(price: float, has_discount: bool) -> float:
    # Assume 10% discount on all items for simplicity
    return float(price) * 0.9 if has_discount else price

# define the expected type of the UDF's parameters
parameters = ['DECIMAL(7, 2)', kuzu.Type.BOOL]

# define expected type of the UDF's returned value
return_type = 'DECIMAL(7, 2)'

# register the UDF
conn.create_function(
    "current_price",
    calculate_discounted_price,
    parameters,
    return_type)
```

The second parameter is a built-in native type in Kuzu, i.e., `kuzu.Type.BOOL`. For the first parameter,
we need to specify a string, i.e. `"DECIMAL(7,2)"` that's then parsed and used by the binder in Kuzu
to map to the internal Decimal representation.