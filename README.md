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


## Development

prerequisites
```
pip install --upgrade pip setuptools wheel
pip install tqdm
pip install -upgrade twine
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