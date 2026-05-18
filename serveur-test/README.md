# Serveur de test local -- Formatif FINAL-AHT20

Ce dossier contient un **serveur Flask compile** (`app.pyc`) que
vous pouvez lancer sur **votre Pi** pour tester votre client REST
sans dependre du serveur de l'instructeur.

Le code source n'est **pas distribue** : les seuils exacts de
decision (`sec`/`confort`/`humide`) restent caches. Vous pouvez
juste verifier que votre client envoie/recoit correctement, sans
voir les valeurs cibles.

> Note : le jour du sommatif, vous interrogerez un serveur fourni
> par l'instructeur (probablement avec d'autres seuils). Ce
> serveur de test sert uniquement a debugger votre client.

## Pre-requis

- Python **3.11** (le .pyc est compile en 3.11, ne fonctionne pas
  avec une autre version mineure)
- `uv` (Astral)

Ce dossier contient deja un `pyproject.toml` et un `.python-version`
qui pinnent la bonne version.

## Lancement

Dans **un autre terminal** (en parallele de votre `main.py`) :

```bash
cd serveur-test
uv sync                                       # installe Flask 3.11
uv run flask --app app run --host 127.0.0.1 --port 8000
```

Le serveur ecoute alors sur `http://127.0.0.1:8000`. Dans votre
`main.py`, mettez :

```python
BASE_URL = "http://127.0.0.1:8000"
```

## Endpoints

Identiques au serveur de l'instructeur (au format pres -- les
valeurs de seuils peuvent differer le jour J).

### `GET /sante`

Sanity check. Aucun parametre.

```json
{"ok": true, "service": "evaluer-aht20-formatif"}
```

### `GET /config`

Retourne les seuils courants du serveur. Purement informatif --
utile pour debugger localement, mais **ne fiez-vous pas a ces
valeurs** : le serveur de l'instructeur le jour du sommatif aura
ses propres seuils.

```json
{"seuil_humide": 65.0, "seuil_sec": 35.0, "unite": "%HR"}
```

### `POST /evaluer`

Categorise une mesure stable d'humidite.

Header obligatoire : `Content-Type: application/json`.

Body JSON :

| Champ | Type | Obligatoire | Description |
|-------|------|:-----------:|-------------|
| `valeur` | float | oui | humidite relative mesuree (%) -- VALEUR PRINCIPALE |
| `duree_stable` | float | oui | secondes de stabilite |
| `temperature` | float | oui | temperature courante (C), valeur secondaire |
| `student_id` | str | recommande | votre numero d'etudiant |

Reponse :

```json
{
  "decision": "sec" | "confort" | "humide",
  "valeur_recue": 50.0,
  "seuil_humide": 65.0,
  "seuil_sec": 35.0
}
```

Codes possibles :

| Code | Cause |
|------|-------|
| 200  | OK |
| 400  | JSON invalide ou champ `valeur` manquant/non numerique |
| 415  | `Content-Type` n'est pas `application/json` |

Voir `code-de-base/README.md` (dossier parent) et
les exemples `curl` ci-dessous.

## Categories de decision

Le serveur classe votre mesure d'humidite dans une des trois
categories :

- `sec`     -> humidite basse (en dessous d'un seuil bas)
- `confort` -> humidite dans la zone de bien-etre (entre les deux seuils)
- `humide`  -> humidite elevee (au-dessus d'un seuil haut)

**Les seuils exacts ne sont pas reveles.** A vous de tester avec
plusieurs valeurs pour cerner les frontieres -- envoyez par
exemple 20 %, 40 %, 60 %, 80 % et observez ou les transitions
se produisent.

> Le jour du sommatif, le serveur de l'instructeur utilisera des
> seuils potentiellement differents. Votre code doit fonctionner
> independamment des valeurs precises : lisez ce que le serveur
> retourne dans `decision`, ne faites pas d'hypothese en dur sur
> les seuils dans votre `main.py`.

## Journal local

Chaque requete `POST /evaluer` est ecrite dans `journal.csv` (a
cote de ce README). Utile pour visualiser ce que votre client
envoie :

```bash
column -t -s, journal.csv | less -S
```

Le fichier est exclu de Git via le `.gitignore` local (vos donnees
de test ne sont pas committees).

Pour reset : `rm journal.csv` (l'en-tete sera recreee a la prochaine
requete).

## Arret du serveur

Ctrl+C dans le terminal du serveur. Si bloque :

```bash
pkill -f "flask --app app"
```

## Pourquoi un .pyc et pas un .py ?

Le .pyc est du **bytecode CPython** equivalent au .py source mais
**non trivialement lisible**. Vous pouvez l'importer et le lancer,
mais pas en lire directement le code. C'est volontaire : la logique
de seuils reste opaque, ce qui vous force a tester par essais
successifs (et a coder correctement votre client REST plutot que
de coder en dur les seuils dans votre `main.py`).
