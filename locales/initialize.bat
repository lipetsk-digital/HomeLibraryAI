pybabel extract --input-dirs=. --no-wrap --keyword=_ --keyword=_translate_ -k _:1,1t -k _:1,2 -o locales/messages.pot
pybabel init --no-wrap -i locales/messages.pot -d locales -D messages -l en
pybabel init --no-wrap -i locales/messages.pot -d locales -D messages -l ru
pybabel compile -d locales -D messages

pybabel update -d locales -D messages -i locales/messages.pot