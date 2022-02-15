rm -f -r tileget.egg-info/* dist/*
python setup.py sdist
python setup.py bdist_wheel
twine upload --repository pypi dist/*
