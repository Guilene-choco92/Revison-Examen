"""
Mini-examen blanc APDS-9960 -- Capteur APDS + REST
Cours 243-413-SH


Valeur principale envoyée : luminosité (Clear)
Valeur secondaire envoyée : rouge (R)
"""

import time
import board
import adafruit_apds9960.apds9960
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://127.0.0.1:8000"
STUDENT_ID = "206343124"
TIMEOUT_HTTP = 2.0

PERIODE_LECTURE = 0.5
DUREE_STABLE_REQUISE = 3.0
DELTA_STABILITE = 20.0        # amplitude luminosité max-min tolérée
PERIODE_MIN_ENTRE_POSTS = 5.0
TAILLE_HISTORIQUE = 16


# =============================================================================
# PHASE 1 : Acquisition I2C
# =============================================================================

def initialiser_capteur():
    """Initialise le bus I2C et le capteur APDS-9960."""
    try:
        i2c = board.I2C()
        capteur = adafruit_apds9960.apds9960.APDS9960(i2c)
        capteur.enable_color = True
        return capteur
    except Exception:
        print("Impossible d'initialiser le capteur APDS-9960")
        return None


def lire_capteur(capteur):
    """Lit (luminosite, rouge) du APDS-9960."""
    try:
        r, g, b, c = capteur.color_data
        luminosite = float(c)
        rouge = float(r)
        return luminosite, rouge
    except Exception:
        print("Lecture du capteur APDS impossible")
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
    """POST /evaluer avec payload JSON (adapté APDS, sans temperature)."""
    try:
        url = base_url + "/evaluer"

        payload = {
            "valeur": float(valeur),          # luminosité Clear
            "duree_stable": float(duree_stable),
            "secondaire": float(secondaire),  # rouge (R)
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


def afficher(luminosite, rouge, duree_stable, derniere_decision):
 
    print("L=", round(luminosite, 1), "lux", end=" | ")
    print("R=", round(rouge, 1), end=" | ")
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
                luminosite, rouge = lire_capteur(capteur)

                historique.append(luminosite)
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
                            luminosite,
                            duree_stable,
                            rouge
                        )
                        dernier_post = maintenant

                        if decision is not None:
                            derniere_decision = decision

                afficher(luminosite, rouge, duree_stable, derniere_decision)

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
            print("Impossible d'initialiser le capteur APDS-9960.")
            return

        if not verifier_sante(BASE_URL):
            print("Le serveur ne répond pas (GET /sante).")
            return

        #print("Capteur OK, serveur OK. Début de la boucle...\n")

        boucle_principale(capteur, BASE_URL)

    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur (Ctrl+C).")
        print("Fermeture propre du programme.")


if __name__ == "__main__":
    main()
