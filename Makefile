.PHONY: demo test
demo:
	sh ./demo
test:
	python3 -m unittest discover -s tests -v
