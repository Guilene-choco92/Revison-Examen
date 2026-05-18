# Formatif FINAL-AHT20 -- Capteur AHT20 + decision REST

Cours 243-413-SH -- Objets connectes et mobilite
Duree: 2 heures | Ponderation: 35%

---

## Votre configuration

- **Numero d'etudiant:** `1234567` (remplacez par votre numero d'etudiant a 7 chiffres dans `STUDENT_ID`)
- **Serveur de decision:** `http://127.0.0.1:8000` (URL différente lors de l'examen)
- **Pas d'authentification**

Modifiez `BASE_URL` et `STUDENT_ID` dans `main.py`.

> **Tester votre client sans le serveur instructeur** : vous avez
> aussi un serveur Flask compile dans le dossier `serveur-test/`
> que vous pouvez lancer localement sur votre Pi. Voir
> `serveur-test/README.md` pour les instructions. Quand le serveur
> local tourne, mettez `BASE_URL = "http://127.0.0.1:8000"` dans
> `main.py`.

---

## Scenario

Vous developpez un **client de mesure ambiante** qui interroge un
**serveur de decision** distant via HTTP. Votre Raspberry Pi lit
cycliquement l'humidite et la temperature du capteur AHT20. Quand
l'humidite reste stable suffisamment longtemps, vous envoyez la
mesure au serveur, qui retourne une categorie (`sec`, `confort`,
`humide`) que vous affichez en console.

```
   +-----------+   lecture I2C 2 Hz   +-----------+
   |  AHT20    | -------------------> |  Pi       |
   +-----------+                      |  client   |
                                      +-----------+
                                          |  POST /evaluer
                                          |  {valeur (humidite), duree_stable, temperature}
                                          v
                                      +-----------+
                                      |  Serveur  |
                                      |  Flask    |
                                      +-----------+
                                          |  {"decision": "humide"}
                                          v
                                      [affichage console]
```

**Interaction physique** : soufflez doucement sur le AHT20 pour
faire monter l'humidite. Apres ~3 secondes de stabilite dans la
nouvelle plage, la decision `humide` doit revenir. Eloignez-vous
pour observer la redescente et une nouvelle decision (`confort`
ou `sec`).

---

## Endpoints disponibles sur le serveur API REST

### GET `/sante`

Permet de verifier que le serveur est en ligne. Si `service` n'est
pas `evaluer-aht20-formatif`, vous devez arreter votre programme
car il y a un probleme.

Reponse : `200 OK` avec `{"ok": true, "service": "evaluer-aht20-formatif"}`.

### GET `/config` (optionnel)

Permet de recuperer les seuils et l'unite du serveur (purement
informatif -- les seuils peuvent etre differents le jour du sommatif).

Reponse : `{"seuil_humide": 65.0, "seuil_sec": 35.0, "unite": "%HR"}`.

### POST `/evaluer`

Envoie une mesure stable et recoit la decision.

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `valeur` | float | oui | **Humidite** stable mesuree (%) -- VALEUR PRINCIPALE |
| `duree_stable` | float | oui | Duree de stabilite effective (secondes) |
| `temperature` | float | oui | Temperature courante (Celsius) -- valeur secondaire |
| `student_id` | str | recommande | Votre numero d'etudiant |

Exemple de payload :

```json
{
  "valeur": 72.5,
  "duree_stable": 3.2,
  "temperature": 24.1,
  "student_id": "1234567"
}
```

Exemple de reponse :

```json
{
  "decision": "humide",
  "valeur_recue": 72.5,
  "seuil_humide": 65.0,
  "seuil_sec": 35.0
}
```

Codes possibles : `200` (OK), `400` (JSON invalide ou champ manquant),
`415` (Content-Type non JSON).


---

## Branchement des composants

| Composant | Pin RPi (Board) | GPIO (BCM) | Fonction |
|-----------|-----------------|------------|----------|
| AHT20 VCC | Pin 1 | 3.3V | Alimentation capteur |
| AHT20 GND | Pin 9 | GND | Masse capteur |
| AHT20 SDA | Pin 3 | GPIO 2 (SDA1) | Donnees I2C |
| AHT20 SCL | Pin 5 | GPIO 3 (SCL1) | Horloge I2C |

Aucun actionneur. La "decision" est purement logicielle.

---

## Phases de l'examen

### Phase 1 - Acquisition I2C (25 pts)

- Capteur AHT20 via `adafruit_ahtx0.AHTx0(board.I2C())`.
- Lecture de `.relative_humidity` (float en %) -- **valeur principale**
  pour ce formatif.
- Lecture de `.temperature` (float en Celsius) -- valeur secondaire,
  transmise dans le payload.
- Pas de conversion manuelle : la bibliotheque gere tout.

### Phase 2 - Client REST (35 pts)

- Module `requests` (synchronisme classique).
- `GET /sante` au demarrage avec **timeout obligatoire** (typ. 2 s).
- `POST /evaluer` avec payload JSON conforme.
- Parsing de la reponse via `.json()`.
- Verification du code HTTP (`.raise_for_status()` ou
  `.status_code`).
- **Tous les appels** doivent etre dans un bloc `try/except` pour
  attraper `requests.RequestException` (timeout, ConnectionError).

### Phase 3 - Minuteur + stabilite (40 pts)

- Boucle non-bloquante : **aucun `time.sleep(...)` superieur a
  50 ms**. Un `time.sleep(0.01)` pour ne pas surcharger le CPU est
  tolere.
- Cadence des lectures via `time.monotonic()` :
  - Lecture toutes les `PERIODE_LECTURE` secondes.
- Historique glissant des dernieres lectures (timestamp + valeur).
- **Detection de stabilite** : la fenetre est stable si
  `max(H) - min(H) <= DELTA_STABILITE` sur >= `DUREE_STABLE_REQUISE`
  secondes (H = humidite, valeur principale).
- **Anti-rebond** : pas plus d'un `POST /evaluer` toutes les
  `PERIODE_MIN_ENTRE_POSTS` secondes.
- Affichage temps reel sur une ligne :

      H= 48.5 % | T= 24.8 C | stable= 1.5 s | decision= confort

---

## Contraintes importantes

* **Timeout obligatoire** sur chaque appel `requests` (lever
  rapidement si le serveur ne repond pas).
* **Aucun `time.sleep` superieur a 50 ms** dans `boucle_principale`.
* **Gestion d'erreurs reseau** : un POST qui echoue ne doit pas
  faire planter la boucle.
* `time.monotonic()` obligatoire pour la cadence (pas `time.time()`
  qui peut sauter avec un changement d'heure systeme).

---

## Aide disponible (`aide.pyc`)

Un module **`aide.pyc`** (bytecode Python 3.11 compile) vous
accompagne. Il fournit des implementations de reference pour
chaque sous-fonctionnalite : capteur AHT20, client REST,
detection de stabilite, affichage.

Le code source est **non distribue** : vous pouvez importer et
appeler les fonctions, mais pas en lire l'implementation.

**Penalite** : chaque fonction de `aide` que vous appelez **annule
les points** de la sous-fonctionnalite correspondante dans
l'indicateur IND-00SX-D (Programmation, qui pese 45% de la note).

| Fonction d'aide | Points perdus si utilisee |
|---|---|
| `creer_capteur_aht20` | 5 / 45 |
| `lire_aht20` | 6 / 45 |
| `verifier_sante` | 5 / 45 |
| `envoyer_evaluation` | 8 / 45 |
| `traiter_reponse` | 4 / 45 |
| `est_stable` | 8 / 45 |
| `boucle_monotone` | 6 / 45 |
| `afficher_etat` | 3 / 45 |

> Utiliser TOUT `aide` = perdre les 45/100 de IND-00SX-D, mais les
> autres indicateurs (environnement, validation, Git, conformite,
> analyse = 55/100) restent acquis. Strategie de **dernier recours**
> seulement -- l'objectif est d'implementer vous-meme.

L'instructeur detecte l'usage de `aide` par `grep -E 'import aide|aide\.'`
dans votre `main.py`.

Exemple :

```python
import aide

def lire_capteur(capteur):
    return aide.lire_aht20(capteur)   # -6 pts sur "Lecture humidite"
```

La grille d'evaluation complete (`GRILLE_EVALUATION.md`) sera
fournie par votre instructeur (hors de ce depot).

Fonctions disponibles : `creer_capteur_aht20`, `lire_aht20`,
`verifier_sante`, `envoyer_evaluation`, `traiter_reponse`, `est_stable`,
`boucle_monotone`, `afficher_etat`.

---

## Installation des dependances

### Version Python requise : **3.11 obligatoire**

Ce projet **doit** etre execute avec **Python 3.11** (version par
defaut du Raspberry Pi OS Bookworm). Le module d'aide compile
fourni (`aide.pyc`) est un bytecode CPython 3.11 et **ne s'importe
pas** sous une autre version mineure (3.10, 3.12, etc.).

La version est fixee dans deux endroits :
- `.python-version` (lue automatiquement par `uv`)
- `pyproject.toml` : `requires-python = "==3.11.*"`

### Avec uv (recommande)

Le projet utilise **uv** (Astral) pour gerer Python et les
dependances. uv lit `.python-version` et installe Python 3.11 si
besoin, puis cree un environnement virtuel isole.

Lien officiel pour pinner la version Python avec uv :
<https://docs.astral.sh/uv/concepts/python-versions/>

```bash
# Installation des deps (utilise Python 3.11 automatiquement)
uv sync

# Verifier la version utilisee
uv run python --version
# attendu : Python 3.11.x

# Executer le programme
uv run python main.py
```

Si `uv` n'est pas installe sur votre Pi :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Sans uv (deconseille)

Si vous tenez a utiliser `pip` directement :

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install adafruit-blinka adafruit-circuitpython-ahtx0 requests
python main.py
```

### Module `aide.pyc`

Le module d'aide est fourni sous forme **compilee** (`aide.pyc`).
Vous pouvez l'importer normalement (`import aide`) ; le code source
n'est pas distribue. Toute fonction `aide.X` que vous appelez fait
perdre les points de la sous-fonctionnalite correspondante.

---

## Validation locale

```bash
uv run pytest tests/test_validation.py -v
```

Les tests verifient la **structure** de votre code (noms de
fonctions, signatures, constantes, presence de `timeout=`,
absence de `time.sleep` long, presence de `try/except`,
utilisation de `time.monotonic()`). Ils ne verifient ni les
seuils numeriques, ni les details d'implementation : vous devez
les deduire des docstrings et du present README.

Un test qui echoue vous dit **quoi** structurer, pas **comment**.

---

## Tester votre client en conditions reelles

Le dossier `serveur-test/` contient un **serveur Flask compile**
(`app.pyc`) que vous pouvez lancer **localement sur votre Pi**
pour tester votre client REST sans dependre du serveur instructeur.

Le code source du serveur n'est **pas distribue** : les seuils de
decision (`sec`/`confort`/`humide`) restent caches. Vous testez
votre client en envoyant des valeurs et en observant les decisions
retournees.

Dans **un terminal separe** :

```bash
cd serveur-test
uv sync                                                # Flask + Python 3.11
uv run flask --app app run --host 127.0.0.1 --port 8000
```

Dans votre `main.py`, mettez :

```python
BASE_URL = "http://127.0.0.1:8000"
```

Et dans un **3e terminal** ou dans le meme, lancez votre client :

```bash
uv run python main.py
```

Chaque `POST /evaluer` est journalise dans `serveur-test/journal.csv`
(timestamp, IP, student_id, valeur, decision). Utile pour debugger
ce que votre client envoie reellement.

Voir `serveur-test/README.md` pour le schema complet des endpoints
et les categories de decision.

> Le jour du sommatif, vous interrogerez le serveur de l'instructeur
> a l'URL fournie. Les seuils peuvent etre differents -- votre code
> doit lire `decision` dans la reponse, **pas** coder en dur les
> seuils.

---

## Fonctions a implementer

Voir `main.py` : chaque fonction a une signature et un docstring.
Remplacez les `pass` par votre implementation.

Liste des fonctions :

| Fonction | Phase | Description |
|----------|-------|-------------|
| `initialiser_capteur()` | 1 | Init bus I2C + AHT20 |
| `lire_capteur(capteur)` | 1 | Retourne `(humidite, temperature)` -- humidite d'abord (valeur principale) |
| `verifier_sante(base_url)` | 2 | GET /sante avec timeout |
| `envoyer_mesure(base_url, valeur, duree_stable, temperature)` | 2 | POST /evaluer (valeur = humidite) |
| `est_stable(historique, delta_max)` | 3 | Logique de stabilite sur l'humidite |
| `afficher(humidite, temperature, duree_stable, derniere_decision)` | 3 | Print sur \r |
| `boucle_principale(capteur, base_url)` | 3 | Boucle non-bloquante |
| `main()` | toutes | Orchestration generale |
