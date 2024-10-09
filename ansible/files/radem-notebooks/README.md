## Instaling dependencies and running
### Notebooks
We use [poetry](https://python-poetry.org/) for package management. To enter a virtual enviroment with all dependencies installed run
```bash
poetry install --no-root
poetry shell
```

Alternatively you can run a jupyter notebook directly without entering `poetry shell` with:
```bash
poetry run jupyter notebook
```


### Enviroment variables
For all notebooks to run correctly some secrets must be provided throught a `.env` file. The top level directory contains a `.env.example` file with all the required fileds for an `.env` file.