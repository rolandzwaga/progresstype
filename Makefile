.PHONY: build clean install venv

venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

install:
	.venv/bin/pip install -r requirements.txt

build:
	.venv/bin/python sources/build.py

clean:
	rm -rf fonts/*.ttf fonts/*.woff2
