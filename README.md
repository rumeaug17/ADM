# ADM
Gestion d'un catalogue d'application avec classification et score de dette

Il s'agit d'uner petite application toute simple (très primitive) servant à expliquer et démontrer l'intérêt d'une telle application pour la gestion de la dette applicative dans une DSI.

L'objectif d'une telle application est de calculer une estimation de la dette d'un SI application par application, afin d'avoir un état des lieux factuel, facilitant la prise de décision et permettant d'identifier là où un effort doit être prévu.

Les questions pour l'estimation du score de dette pour chaque application est configurable dans un fichier json. Celles sont modifiables.

# INSTALL and RUN:
```
pip install -r requirements.txt
% --proxy=http://USER:PWD@PROXY:PORT
git describe --tags --abbrev=0 > static/version.txt

python app.py
http://127.0.0.1:5000/
```
# site de démo
https://rg17.pythonanywhere.com/
