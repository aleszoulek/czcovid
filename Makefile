build:
	curl https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/umrti.json > umrti.json
	curl https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani.json > ockovani.json
	python main.py
	git status
	git commit -a -m 'data update'
