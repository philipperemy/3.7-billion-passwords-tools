all:
	make install

install:
	pip install cython pytest
	python setup.py build_ext --inplace
	pip install . --upgrade

uninstall:
	pip uninstall -y breach

test:
	pytest tests

clean:
	rm -rf *.out breach/*.c *.bin *.exe *.o *.a breach/*.so build *.html __pycache__ breach/__pycache__
