"""
Mini-examen blanc VCNL4200 -- Capteur VCNL + REST
Cours 243-413-SH

Valeur principale envoyée : proximite 
Valeur secondaire envoyée : luminosite 
"""

import time
import board
import adafruit_vcnl4040
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://127.0.0.1:8000"
STUDENT_ID = "206343124"
TIMEOUT_HTTP = 2.0

PERIODE_LECTURE = 0.5
DUREE_STABLE_REQUISE = 3.0
DELTA_STABILITE = 200

PERIODE_MIN_ENTRE_POSTS = 5.0
TAILLE_HISTORIQUE = 16


# =============================================================================
# PHASE 1 : Acquisition I2C
# =============================================================================

def initialiser_capteur():
    """Initialise le bus I2C et le capteur VCNL."""
    try:
        i2c = board.I2C()
        capteur = adafruit_vcnl4040.VCNL4040(i2c)
        return capteur
    except Exception:
        print("Impossible d'initialiser le capteur VCNL4200")
        return None


def lire_capteur(capteur):
    """Lit (proximite, luminosite) du VCNL."""
    try:
        proximite = float(capteur.proximity) 
        luminosite = float(capteur.lux)
        return proximite, luminosite
    except Exception:
        print("Lecture du capteur VCNL impossible")
        return 0.0, 0.0


# =============================================================================
# PHASE 2 : Client REST
# =============================================================================

def verifier_sante(base_url):
    """GET /sante -- retourne True si le serveur repond avec ok."""
    try:
        url = base_url + "/sante"
        reponse = requests.get(url, timeout=TIMEOUT_HTTP)

        if reponse.status_code == 200:
            donnee = reponse.json()
            if "ok" in donnee and donnee["ok"] is True:
                return True

        return False
    except Exception:
        print("Serveur injoignable (GET /sante)")
        return False


def envoyer_mesure(base_url, valeur, duree_stable, secondaire):
    """POST /evaluer avec payload JSON (adapté VCNL4200)."""
    try:
        url = base_url + "/evaluer"

        payload = {
            "valeur": float(valeur),          # proximite
            "duree_stable": float(duree_stable),
            "secondaire": float(secondaire),  # luminosite
            "student_id": STUDENT_ID
        }

        reponse = requests.post(url, json=payload, timeout=TIMEOUT_HTTP)

        if reponse.status_code == 200:
            data = reponse.json()
            if "decision" in data:
                return data["decision"]

        return None

    except Exception:
        print("Impossible d'envoyer la mesure (POST /evaluer)")
        return None


# =============================================================================
# PHASE 3 : Minuteur + stabilité
# =============================================================================

def est_stable(historique, delta_max):
    """Retourne True si la fenêtre est stable (max-min <= delta_max)."""
    if len(historique) < 2:
        return False

    valeur_max = max(historique)
    valeur_min = min(historique)

    return (valeur_max - valeur_min) <= delta_max


def afficher(proximite, luminosite, duree_stable, derniere_decision):
    """Affiche une ligne console rafraîchie."""
    print("P=", round(proximite, 1), end=" | ")
    print("Lux=", round(luminosite, 1), end=" | ")
    print("stable=", round(duree_stable, 1), "s", end=" | ")
    print("decision=", derniere_decision, end="\r")


def boucle_principale(capteur, base_url):
    """Boucle non-bloquante à time.monotonic()."""
    historique = []
    derniere_decision = None

    dernier_temps_lecture = 0
    debut_stable = None
    dernier_post = 0

    while True:
        maintenant = time.monotonic()

        if maintenant - dernier_temps_lecture >= PERIODE_LECTURE:
            dernier_temps_lecture = maintenant

            try:
                proximite, luminosite = lire_capteur(capteur)

                historique.append(proximite)
                if len(historique) > TAILLE_HISTORIQUE:
                    historique.pop(0)

                if est_stable(historique, DELTA_STABILITE):
                    if debut_stable is None:
                        debut_stable = maintenant
                    duree_stable = maintenant - debut_stable
                else:
                    debut_stable = None
                    duree_stable = 0

                if duree_stable >= DUREE_STABLE_REQUISE:
                    if maintenant - dernier_post >= PERIODE_MIN_ENTRE_POSTS:
                        decision = envoyer_mesure(
                            base_url,
                            proximite,
                            duree_stable,
                            luminosite
                        )
                        dernier_post = maintenant

                        if decision is not None:
                            derniere_decision = decision

                afficher(proximite, luminosite, duree_stable, derniere_decision)

            except:
                print("\nErreur pendant la boucle")

        time.sleep(0.01)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Init capteur + verif serveur + boucle. Arrêt propre sur Ctrl+C."""
    try:
        capteur = initialiser_capteur()
        if capteur is None:
            print("Impossible d'initialiser le capteur VCNL4200.")
            return

        if not verifier_sante(BASE_URL):
            print("Le serveur ne répond pas (GET /sante).")
            return



        boucle_principale(capteur, BASE_URL)

    except KeyboardInterrupt:

        print("Fermeture propre du programme.")


if __name__ == "__main__":
    main()
