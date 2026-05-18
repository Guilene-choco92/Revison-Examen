"""
Formatif FINAL-AHT20 -- Mini-examen blanc, capteur AHT20 + REST
Cours 243-413-SH

Variante FORMATIVE de l'examen FINAL-AHT20. Meme architecture
(lecture I2C, client REST, boucle non-bloquante a time.monotonic)
mais **sujet variant** pour eviter le copier-coller :

* Valeur principale envoyee au serveur : **humidite relative** (%)
  au lieu de la temperature.
* Endpoint serveur : **/evaluer** au lieu de /decider.
* Decisions : **"sec" | "confort" | "humide"** au lieu de
  chaud/normal/froid.

Interaction physique
--------------------
Soufflez doucement sur le capteur AHT20 ; l'humidite mesuree monte.
Eloignez-vous pour la voir redescendre. Apres stabilisation, le
serveur renvoie une categorie d'humidite.

Contrat REST (resume)
---------------------
* GET  `<BASE_URL>/sante`     -> `{"ok": true, ...}`
* POST `<BASE_URL>/evaluer`   -> payload :
    `{"valeur": float, "duree_stable": float, "temperature": float,
      "student_id": str}`
  reponse :
    `{"decision": "sec"|"confort"|"humide", ...}`

Contraintes (identiques au sommatif)
------------------------------------
* Aucun `time.sleep` superieur a 50 ms dans `boucle_principale`.
* Timeout obligatoire sur chaque appel `requests`.
* Gestion d'erreurs reseau (la boucle ne plante pas).
* Anti-rebond entre POST consecutifs.

Aide (`aide.pyc`)
-----------------
Module compile Python 3.11 fourni ; usage penalise. Voir
GRILLE_EVALUATION.md fournie par l'instructeur.
"""

import time

import board
import adafruit_ahtx0
import requests


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://192.168.1.100:8000"
STUDENT_ID = "1234567"                    # Votre numero d'etudiant (7 chiffres)
TIMEOUT_HTTP = 2.0

PERIODE_LECTURE = 0.5
DUREE_STABLE_REQUISE = 3.0
DELTA_STABILITE = 1.5            # amplitude humidite max-min toleree (%)
PERIODE_MIN_ENTRE_POSTS = 5.0
TAILLE_HISTORIQUE = 16


# =============================================================================
# PHASE 1 : Acquisition I2C (25 pts)
# =============================================================================


def initialiser_capteur():
    """Initialise le bus I2C et le capteur AHT20.

    Returns:
        adafruit_ahtx0.AHTx0: instance du capteur.
    """
    pass


def lire_capteur(capteur):
    """Lit (humidite, temperature) du AHT20.

    Note : dans ce formatif, **l'humidite est la valeur principale**
    (envoyee au serveur). La temperature est lue en passant et
    sert de champ secondaire dans le payload.

    Args:
        capteur: instance `adafruit_ahtx0.AHTx0`.

    Returns:
        tuple[float, float]: (humidite en %, temperature en C).
    """
    pass


# =============================================================================
# PHASE 2 : Client REST (35 pts)
# =============================================================================


def verifier_sante(base_url):
    """GET /sante -- retourne True si le serveur repond avec ok."""
    pass


def envoyer_mesure(base_url, valeur, duree_stable, temperature):
    """POST /evaluer avec payload JSON.

    Payload :
        {"valeur": float (humidite), "duree_stable": float,
         "temperature": float, "student_id": STUDENT_ID}

    Returns:
        str | None: la decision ("sec"/"confort"/"humide"), ou None
        sur erreur.
    """
    pass


# =============================================================================
# PHASE 3 : Minuteur + stabilite (40 pts)
# =============================================================================


def est_stable(historique, delta_max):
    """Retourne True si la fenetre `historique` est stable
    (max - min <= delta_max).

    Pour historique vide ou de longueur < 2 : False.
    """
    pass


def afficher(humidite, temperature, duree_stable, derniere_decision):
    """Affiche une ligne console (rafraichie avec \\r).

    Format suggere :
        H= 48.5 % | T= 24.8 C | stable= 1.5 s | decision= confort
    """
    pass


def boucle_principale(capteur, base_url):
    """Boucle non-bloquante a `time.monotonic()`.

    Identique au sommatif : historique glissant, detection de
    stabilite, POST anti-rebond, affichage.
    """
    pass


# =============================================================================
# POINT D'ENTREE
# =============================================================================


def main():
    """Init capteur + verif serveur + boucle. Arret propre sur Ctrl+C."""
    pass


if __name__ == "__main__":
    main()
