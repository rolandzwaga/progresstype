.PHONY: build clean install venv serve

venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

install:
	.venv/bin/pip install -r requirements.txt

build:
	.venv/bin/python sources/build.py

serve:
	.venv/bin/python dev/server.py

clean:
	rm -rf fonts/variable/* fonts/ttf/* fonts/webfonts/*
