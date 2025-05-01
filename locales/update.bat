pybabel extract --input-dirs=. --no-wrap --keyword=_ --keyword=_translate_ -o locales/messages.pot
pybabel update --no-wrap -d locales -D messages -i locales/messages.pot
pybabel compile -d locales -D messages
