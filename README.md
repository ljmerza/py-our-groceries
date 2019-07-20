Unofficial asyncio python wrapper for the Our Groceries API. This library requires `Python >=3.5`.

## Installation

```bash
pip install ourgroceries
```

## Usage

```
from ourgroceries import OurGroceries

username = ''
password = ''

og = OurGroceries(username, password)
my_lists = og.get_my_lists()
my_todo_list = og.get_list_items(list_id='')
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