Unofficial asyncio python wrapper for the Our Groceries API. This library requires `Python >=3.5`.

## Installation

```bash
pip install ourgroceries
```

## Usage

```
import OurGroceries from ourgroceries

username = ''
password = ''

og = OurGroceries(username, password)
my_lists = og.get_my_lists()
my_todo_list = og.get_list_items(list_id='')
```


## Development

prerequisites
```
python -m pip install --upgrade pip setuptools wheel
python -m pip install tqdm
python -m pip install --user --upgrade twine
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
python -m twine upload dist/*
```