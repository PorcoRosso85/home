import json
from pycozo.client import Client
from .query.ddl import create_all_schemas

def main():
    client = Client()

    try:
        results = create_all_schemas(client)
        print("results", results)
    except Exception as e:
        print(repr(e))

    finally:
        client.close()


if __name__ == "__main__":
    main()
