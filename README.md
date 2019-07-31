Unofficial asyncio python wrapper for the Our Groceries API. This library requires `Python >=3.5`.

## Installation

```bash
pip install ourgroceries
```

## Usage

```
import asyncio
from ourgroceries import OurGroceries

username = ''
password = ''

og = OurGroceries(username, password)
asyncio.run(og.login())

my_lists = asyncio.run(og.get_my_lists())
print(my_lists)

my_todo_list = asyncio.run(og.get_list_items(list_id=''))
print(my_todo_list)
```

## Methods
```def login()```

Logs into our groceries

---

```def get_my_lists()```

Gets all of your lists

---

```def get_list_items(list_id)```

Gets the items for a list

---

```def create_list(name, list_type='SHOPPING')```

Creates a new list. list_type can be 'RECIPES' or 'SHOPPING'

---

```def toggle_item_crossed_off(list_id, item_id, cross_off=False)```

Toggle a list item's crossed off property based on `cross_off`

---

```def add_item_to_list(list_id, value)```

Adds a new item to a given list

---

```def remove_item_from_list(list_id, item_id)```

Removes an item from a given list

---


## Exceptions

throws `InvalidLoginException` if can't login.


## Development

prerequisites
```
pip install --upgrade pip setuptools wheel
pip install tqdm
pip install --upgrade twine
```

build
```bash
python setup.py sdist
```

install
```bash
python setup.py install
```

upload
```bash
twine upload dist/*
```