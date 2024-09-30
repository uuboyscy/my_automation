precommit:
	pre-commit run --show-diff-on-failure --color=always --all-files

install:
	poetry add $(package) && poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev

lock:
	poetry lock && poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev
