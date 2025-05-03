run:
	source ./venv/bin/activate && python3 -m framework

venv:
	python3 -m venv venv
	source ./venv/bin/activate && pip install -r requirements.txt

test:
	pytest -v --html=report_tests.html --self-contained-html