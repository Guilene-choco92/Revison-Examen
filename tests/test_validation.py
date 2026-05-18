"""
Tests de pre-validation pour l'examen FINAL-AHT20-FORMATIF.

    pytest tests/test_validation.py -v

Ces tests valident la STRUCTURE de votre code : fonctions definies,
signatures presentes, constantes nommees, usage du timeout, absence
de `time.sleep` long. Ils NE VERIFIENT PAS les valeurs attendues :
vous devez lire les docstrings du squelette et le README pour
deduire les details.

Un test qui echoue vous indique *quoi* structurer, pas *comment*.
"""

import ast
import sys
from pathlib import Path

import pytest

MAIN_PY = Path(__file__).parent.parent / "main.py"


# -----------------------------------------------------------------------------
# Helpers (internes)
# -----------------------------------------------------------------------------

def _source():
    assert MAIN_PY.exists(), (
        "main.py introuvable. Executez pytest depuis la racine du projet."
    )
    return MAIN_PY.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source())


def _functions():
    """Retourne {nom: FunctionDef} pour toutes les fonctions de module."""
    return {
        node.name: node
        for node in _tree().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _has_call(source, name_predicate):
    """Retourne True si un Call dont le nom matche `name_predicate`
    existe dans l'AST."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and name_predicate(func.id):
                return True
            if isinstance(func, ast.Attribute) and name_predicate(func.attr):
                return True
    return False


def _call_has_kwarg(source, name_predicate, kw_name):
    """Retourne True si un Call matchant `name_predicate` contient
    un keyword argument nomme `kw_name`."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            matched = (
                (isinstance(func, ast.Name) and name_predicate(func.id))
                or (isinstance(func, ast.Attribute) and name_predicate(func.attr))
            )
            if matched:
                for kw in node.keywords:
                    if kw.arg == kw_name:
                        return True
    return False


def _body_is_empty(fn):
    """True si le corps de `fn` ne contient que docstring et/ou pass."""
    body = fn.body
    only_docstring = (
        len(body) == 1
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
    )
    only_pass = len(body) == 1 and isinstance(body[0], ast.Pass)
    docstring_then_pass = (
        len(body) == 2
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[1], ast.Pass)
    )
    return only_docstring or only_pass or docstring_then_pass


# -----------------------------------------------------------------------------
# Presence du fichier et des imports materiels
# -----------------------------------------------------------------------------

def test_main_exists():
    """main.py existe a la racine du projet."""
    assert MAIN_PY.exists(), "main.py introuvable."


def test_imports_materiels_presents():
    """Les modules d'acces au capteur sont importes.

    Le squelette fournit deja ces imports : ne les retirez pas.
    """
    src = _source()
    missing = [m for m in ("board", "adafruit_ahtx0") if m not in src]
    assert not missing, (
        f"Imports hardware manquants : {missing}. Consultez le README "
        "pour la liste des modules CircuitPython requis."
    )


def test_import_requests_present():
    """Le client HTTP `requests` est importe."""
    assert "import requests" in _source() or "from requests" in _source(), (
        "Module `requests` non importe : impossible d'appeler le serveur REST."
    )


def test_import_time_present():
    """Le module `time` est importe pour le minuteur monotone."""
    src = _source()
    assert "import time" in src or "from time" in src, (
        "Module `time` non importe : requis pour `time.monotonic()`."
    )


# -----------------------------------------------------------------------------
# Constantes nommees
# -----------------------------------------------------------------------------

def test_constantes_configuration_presentes():
    """Les constantes nommees de configuration sont definies."""
    src = _source()
    required = ("BASE_URL", "PERIODE_LECTURE", "DUREE_STABLE_REQUISE",
                "DELTA_STABILITE")
    missing = [c for c in required if c not in src]
    assert not missing, (
        f"Constantes de configuration manquantes : {missing}. "
        "Consultez le README."
    )


# -----------------------------------------------------------------------------
# Phase 1 : capteur AHT20
# -----------------------------------------------------------------------------

def test_initialiser_capteur_defini():
    """Une fonction `initialiser_capteur` existe."""
    assert "initialiser_capteur" in _functions(), (
        "Fonction `initialiser_capteur` manquante."
    )


def test_lire_capteur_defini():
    """Une fonction `lire_capteur` existe avec >=1 parametre."""
    funcs = _functions()
    assert "lire_capteur" in funcs, "Fonction `lire_capteur` manquante."
    fn = funcs["lire_capteur"]
    assert len(fn.args.args) >= 1, (
        "`lire_capteur` doit accepter au moins le capteur en parametre."
    )


# -----------------------------------------------------------------------------
# Phase 2 : Client REST
# -----------------------------------------------------------------------------

def test_verifier_sante_defini():
    """Une fonction `verifier_sante` existe avec >=1 parametre."""
    funcs = _functions()
    assert "verifier_sante" in funcs, "Fonction `verifier_sante` manquante."
    assert len(funcs["verifier_sante"].args.args) >= 1, (
        "`verifier_sante(base_url)` attendu."
    )


def test_envoyer_mesure_defini():
    """Une fonction `envoyer_mesure` existe avec >=3 parametres."""
    funcs = _functions()
    assert "envoyer_mesure" in funcs, "Fonction `envoyer_mesure` manquante."
    assert len(funcs["envoyer_mesure"].args.args) >= 3, (
        "`envoyer_mesure(base_url, valeur, duree_stable, temperature)` attendu."
    )


def test_requests_get_et_post_utilises():
    """Le code appelle `requests.get` ET `requests.post` au moins une fois."""
    src = _source()
    assert _has_call(src, lambda n: n == "get"), (
        "Aucun `requests.get(...)` trouve : comment verifiez-vous /sante ?"
    )
    assert _has_call(src, lambda n: n == "post"), (
        "Aucun `requests.post(...)` trouve : comment envoyez-vous au serveur ?"
    )


def test_timeout_present_sur_requests():
    """Au moins un appel a `get`/`post` utilise un keyword `timeout=...`."""
    src = _source()
    has_get_timeout = _call_has_kwarg(src, lambda n: n == "get", "timeout")
    has_post_timeout = _call_has_kwarg(src, lambda n: n == "post", "timeout")
    assert has_get_timeout or has_post_timeout, (
        "Aucun `timeout=` trouve sur les appels `requests`. "
        "Specifications.md exige un timeout explicite."
    )


def test_json_parse_present():
    """Le code appelle `.json()` au moins une fois (parsing reponse)."""
    src = _source()
    assert _has_call(src, lambda n: n == "json"), (
        "Aucun `.json()` trouve : comment extrayez-vous la decision ?"
    )


def test_try_except_autour_requests():
    """Au moins un bloc Try englobe un appel `requests`."""
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    name = (
                        (isinstance(func, ast.Name) and func.id)
                        or (isinstance(func, ast.Attribute) and func.attr)
                        or ""
                    )
                    if name in ("get", "post"):
                        return
    pytest.fail(
        "Aucun bloc `try/except` n'englobe un appel `requests.get/post`. "
        "La boucle doit survivre aux erreurs reseau."
    )


# -----------------------------------------------------------------------------
# Phase 3 : Minuteur et stabilite
# -----------------------------------------------------------------------------

def test_time_monotonic_utilise():
    """Le code utilise `time.monotonic()` (pas seulement `time.time`)."""
    src = _source()
    assert "monotonic" in src, (
        "`time.monotonic()` introuvable. Le minuteur de la boucle doit "
        "etre monotone pour ne pas etre affecte par les changements d'heure."
    )


def test_est_stable_defini():
    """Une fonction `est_stable` existe avec >=2 parametres."""
    funcs = _functions()
    assert "est_stable" in funcs, "Fonction `est_stable` manquante."
    assert len(funcs["est_stable"].args.args) >= 2, (
        "`est_stable(historique, delta_max)` attendu."
    )


def test_afficher_defini():
    """Une fonction `afficher` existe."""
    assert "afficher" in _functions(), "Fonction `afficher` manquante."


def test_boucle_principale_definie_non_vide():
    """`boucle_principale` existe et a un corps non vide."""
    funcs = _functions()
    assert "boucle_principale" in funcs, "Fonction `boucle_principale` manquante."
    assert not _body_is_empty(funcs["boucle_principale"]), (
        "Fonction `boucle_principale` a un corps vide (pass). Implementez-la."
    )


def test_pas_de_sleep_long_dans_boucle_principale():
    """`boucle_principale` ne contient pas de `time.sleep(x)` avec x > 0.05.

    Un petit yield (<=0.05 s) pour liberer le CPU est tolere.
    """
    funcs = _functions()
    fn = funcs.get("boucle_principale")
    if fn is None:
        pytest.skip("boucle_principale non definie (test couvert ailleurs)")

    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            attr = getattr(node.func, "attr", None)
            name = getattr(node.func, "id", None)
            if attr == "sleep" or name == "sleep":
                if node.args and isinstance(node.args[0], ast.Constant):
                    val = node.args[0].value
                    if isinstance(val, (int, float)) and val > 0.05:
                        pytest.fail(
                            f"`time.sleep({val})` trouve dans "
                            "`boucle_principale` : valeur trop longue. "
                            "Utilisez `time.monotonic()` pour cadencer et "
                            "limitez sleep <= 0.05 s pour liberer le CPU."
                        )
                else:
                    pytest.fail(
                        "`time.sleep(<variable>)` trouve dans "
                        "`boucle_principale` : argument non litteral, "
                        "impossible de garantir <= 0.05 s. Inlinez la valeur."
                    )


# =============================================================================
# TESTS DE COMPORTEMENT (mockes)
# =============================================================================
#
# Les tests precedents valident la STRUCTURE (AST). Ceux qui suivent
# valident le COMPORTEMENT en appelant reellement vos fonctions avec
# des mocks. Ils ne revelent ni les seuils, ni l'algorithme.
#
# Un mock est un faux objet qui remplace un dependance reseau ou
# hardware. Ici, requests.post et time.monotonic sont remplaces le
# temps du test. Votre code n'a rien a faire de special : du moment
# qu'il appelle ces fonctions normalement, les mocks interceptent.

import importlib


def _import_main():
    """Importe (ou recharge) main pour qu'il prenne les mocks courants."""
    if "main" in sys.modules:
        return importlib.reload(sys.modules["main"])
    import main
    return main


# -----------------------------------------------------------------------------
# Comportement 1 : envoyer_mesure construit le bon payload JSON
# -----------------------------------------------------------------------------

def test_envoyer_mesure_payload_clefs(monkeypatch):
    """envoyer_mesure passe `json=` (pas `data=`) avec les bonnes cles."""
    import requests

    captured = {}

    def capturing_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        captured["json"] = kwargs.get("json")

        class _R:
            status_code = 200

            def json(self_):
                return {"decision": "confort"}

            def raise_for_status(self_):
                pass

        return _R()

    monkeypatch.setattr(requests, "post", capturing_post)

    main = _import_main()
    main.envoyer_mesure("http://test.local", 50.0, 3.5, 25.0)

    assert captured.get("json") is not None, (
        "envoyer_mesure doit passer `json=...` a requests.post "
        "(pas `data=`). Le serveur attend Content-Type: application/json."
    )

    payload = captured["json"]
    for key in ("valeur", "duree_stable"):
        assert key in payload, (
            f"Cle `{key}` manquante dans le payload JSON. "
            "Voir le contrat REST dans README.md."
        )
    # La valeur secondaire est nommee `temperature` dans ce formatif
    # (le sommatif utilisera un autre champ). On verifie juste qu'au
    # moins un champ supplementaire est present.
    extra_keys = set(payload.keys()) - {"valeur", "duree_stable", "student_id"}
    assert extra_keys, (
        "Le payload doit contenir une valeur secondaire (temperature). "
        "Voir le contrat REST dans README.md."
    )


def test_envoyer_mesure_timeout_present(monkeypatch):
    """envoyer_mesure passe un timeout numerique a requests.post."""
    import requests

    captured = {}

    def capturing_post(url, **kwargs):
        captured["kwargs"] = kwargs

        class _R:
            status_code = 200

            def json(self_):
                return {"decision": "confort"}

            def raise_for_status(self_):
                pass

        return _R()

    monkeypatch.setattr(requests, "post", capturing_post)

    main = _import_main()
    main.envoyer_mesure("http://test.local", 50.0, 3.0, 23.0)

    kwargs = captured.get("kwargs") or {}
    assert "timeout" in kwargs, (
        "envoyer_mesure doit specifier un `timeout=...` (lever rapidement "
        "si le serveur ne repond pas)."
    )
    assert isinstance(kwargs["timeout"], (int, float)), (
        "Le `timeout=` doit etre numerique (secondes)."
    )


# -----------------------------------------------------------------------------
# Comportement 2 : est_stable retourne le bon booleen
# -----------------------------------------------------------------------------

def test_est_stable_fenetre_stable():
    """est_stable retourne True quand max-min <= delta_max."""
    main = _import_main()
    result = main.est_stable([50.0, 50.5, 50.2, 49.8], 1.0)
    assert result is True, (
        "Fenetre [50.0, 50.5, 50.2, 49.8] avec delta_max=1.0 doit etre "
        "stable (max-min = 0.7 <= 1.0). Recu : {!r}".format(result)
    )


def test_est_stable_fenetre_instable():
    """est_stable retourne False quand max-min > delta_max."""
    main = _import_main()
    result = main.est_stable([50.0, 60.0, 55.0], 1.0)
    assert result is False, (
        "Fenetre [50.0, 60.0, 55.0] avec delta_max=1.0 doit etre "
        "instable (max-min = 10 > 1.0). Recu : {!r}".format(result)
    )


def test_est_stable_fenetre_trop_petite():
    """est_stable retourne False pour une fenetre vide ou de taille < 2."""
    main = _import_main()
    assert main.est_stable([], 1.0) is False, (
        "Une fenetre vide ne peut pas etre declaree stable."
    )
    assert main.est_stable([50.0], 1.0) is False, (
        "Une fenetre de taille 1 ne peut pas etre declaree stable "
        "(pas assez de points pour mesurer une amplitude)."
    )


# -----------------------------------------------------------------------------
# Comportement 3 : envoyer_mesure attrape les exceptions reseau
# -----------------------------------------------------------------------------

def test_envoyer_mesure_attrape_timeout(monkeypatch):
    """envoyer_mesure retourne None (ne crash pas) si requests leve Timeout."""
    import requests

    appele = [False]

    def raise_timeout(*args, **kwargs):
        appele[0] = True
        raise requests.Timeout("simulated timeout")

    monkeypatch.setattr(requests, "post", raise_timeout)

    main = _import_main()
    try:
        result = main.envoyer_mesure("http://test.local", 50.0, 3.0, 23.0)
    except Exception as e:
        pytest.fail(
            "envoyer_mesure n'a pas attrape l'exception {} : {}. "
            "Une boucle qui plante des qu'un POST echoue n'est pas "
            "robuste -- attrapez `requests.RequestException` (classe "
            "parente de Timeout, ConnectionError, HTTPError, etc.)."
            .format(type(e).__name__, e)
        )

    assert appele[0], (
        "requests.post n'a pas ete appele. envoyer_mesure doit envoyer "
        "une requete reelle."
    )
    assert result is None, (
        "envoyer_mesure doit retourner None apres une exception reseau "
        "(c'est ce qui permet a la boucle de continuer)."
    )


def test_envoyer_mesure_attrape_connection_error(monkeypatch):
    """envoyer_mesure attrape aussi ConnectionError (serveur down)."""
    import requests

    appele = [False]

    def raise_connerr(*args, **kwargs):
        appele[0] = True
        raise requests.ConnectionError("server down")

    monkeypatch.setattr(requests, "post", raise_connerr)

    main = _import_main()
    try:
        result = main.envoyer_mesure("http://test.local", 50.0, 3.0, 23.0)
    except Exception as e:
        pytest.fail(
            "envoyer_mesure n'a pas attrape ConnectionError : {}".format(e)
        )
    assert appele[0], (
        "requests.post n'a pas ete appele. envoyer_mesure doit envoyer "
        "une requete reelle."
    )
    assert result is None


# -----------------------------------------------------------------------------
# Comportement 4 : boucle_principale POST avec anti-rebond
# -----------------------------------------------------------------------------
# Simule 30 secondes virtuelles. Un capteur immobile devrait declencher
# plusieurs POST espaces par PERIODE_MIN_ENTRE_POSTS. Pas plus de ~10
# POSTs sur 30s (anti-rebond), pas moins de 1 (la boucle doit POST).

def test_boucle_principale_anti_rebond(monkeypatch):
    """Sur 30s virtuelles avec capteur stable, anti-rebond limite les POST."""
    import requests

    # --- 1. Faux time.monotonic qui avance par pas de 0.05s ---
    now = [0.0]
    n_ticks = [0]

    def fake_monotonic():
        n_ticks[0] += 1
        if n_ticks[0] > 10000:
            raise KeyboardInterrupt("trop d'iterations (boucle probable)")
        now[0] += 0.05
        if now[0] > 30.0:
            raise KeyboardInterrupt("30s virtuelles ecoulees")
        return now[0]

    monkeypatch.setattr("time.monotonic", fake_monotonic)
    monkeypatch.setattr("time.sleep", lambda s: None)

    # --- 2. Faux capteur stable ---
    class StableCapteur:
        relative_humidity = 50.0
        temperature = 23.0

    # --- 3. Faux requests.post qui compte les appels ---
    posts = []

    def fake_post(url, **kwargs):
        posts.append(kwargs.get("json"))
        if len(posts) > 200:
            raise KeyboardInterrupt("trop de POSTs (anti-rebond absent ?)")

        class _R:
            status_code = 200

            def json(self_):
                return {"decision": "confort"}

            def raise_for_status(self_):
                pass

        return _R()

    monkeypatch.setattr(requests, "post", fake_post)

    main = _import_main()

    try:
        main.boucle_principale(StableCapteur(), "http://test.local")
    except KeyboardInterrupt:
        pass  # sortie attendue
    except SystemExit:
        pass

    nb = len(posts)
    assert nb >= 1, (
        "boucle_principale n'a envoye aucun POST en 30s virtuelles avec "
        "un capteur stable. Verifiez la detection de stabilite et "
        "l'appel a envoyer_mesure."
    )
    assert nb <= 15, (
        "boucle_principale a envoye {} POSTs en 30s virtuelles. "
        "L'anti-rebond (PERIODE_MIN_ENTRE_POSTS) devrait limiter a ~6. "
        "Verifiez que vous memorisez le timestamp du dernier POST."
        .format(nb)
    )
