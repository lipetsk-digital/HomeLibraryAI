pybabel extract --input-dirs=. --no-wrap --keyword=_ --keyword=_translate_ -o locales/messages.pot
pybabel init --no-wrap -i locales/messages.pot -d locales -D messages -l en
pybabel init --no-wrap -i locales/messages.pot -d locales -D messages -l ru
pybabel compile -d locales -D messages

pybabel update -d locales -D messages -i locales/messages.pot