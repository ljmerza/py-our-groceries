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

loop = asyncio.get_event_loop()
loop.run_until_complete(og.login())

my_lists = loop.run_until_complete(og.get_my_lists())
print(my_lists)

my_todo_list = loop.run_until_complete(og.get_list_items(list_id=''))
print(my_todo_list)
```

## Methods
```def login()```

Logs into our groceries

---

```def get_my_lists()```

Gets all of your lists

---

```def get_category_items()```

Gets all of your category items

---

```def get_list_items(list_id)```

Gets the items for a list

---

```def create_list(name, list_type='SHOPPING')```

Creates a new list. list_type can be 'RECIPES' or 'SHOPPING'

---

```def create_category(name)```

Create a new category

---

```def toggle_item_crossed_off(list_id, item_id, cross_off=False)```

Toggle a list item's crossed off property based on `cross_off`

---

```def add_item_to_list(list_id, value, category="uncategorized", auto_category=False, note=None)```

Adds a new item to a given list/category. Use `auto_category` instead of `category` to let
Our Groceries apply the default category for this item.

---

```async def add_items_to_list(self, list_id, items)```

Adds several items to a given list. Use `items` to pass a sequence of items, each being just a value, or a tuple
(value, category, note).

---

```def remove_item_from_list(list_id, item_id)```

Removes an item from a given list

---

```def get_master_list()```

Gets the master list

---

```def get_category_list()```

Gets the category list

---

```def delete_list(list_id)```

Deletes a list

---

```def delete_all_crossed_off_from_list(list_id)```

Deletes all crossed off items from a list

---

```def add_item_to_master_list(value, category_id)```

Adds an item to the master list

---

```def change_item_on_list(list_id, item_id, category_id, value)```

Changes an item on a list

---

## Exceptions

throws `InvalidLoginException` if can't login.


## Development

prerequisites
```
python3 -m pip install --user --upgrade setuptools wheel
python3 -m pip install --user --upgrade twine

increment version in `setup.py`
delete build folder

python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
```
