lint: flake8 mypy
format: yapf isort

mypy:
	mypy --ignore-missing-imports --check-untyped-defs -m tcp

flake8:
	flake8 tcp

yapf:
	yapf -i -r tcp

isort:
	isort tcp

build:
	python3 -m build

test:
	python3 -m tcp.test_stream
	python3 -m tcp.test_reassembler
	python3 -m tcp.test_wrap32
	python3 -m tcp.test_receiver
	python3 -m tcp.test_sender

viz:
	pyreverse -m n -k --colorized -o png tcp
