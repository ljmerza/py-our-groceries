

## Development


prerequisites
```
python -m pip install --upgrade pip setuptools wheel
python -m pip install tqdm
python -m pip install --user --upgrade twine
```


build
```bash
python setup.py bdist_wheel
```

install
```bash
python -m pip install dist/pyourgroceries-0.1-py3-none-any.whl
```

upload
```bash
python -m twine upload dist/*
```
