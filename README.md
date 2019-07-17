

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

install from pip
```
pip install py-our-groceries
