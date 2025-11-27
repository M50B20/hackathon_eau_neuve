from ursina import *
import random

app = Ursina()

# --- MISE EN PLACE DE LA SCÈNE ---
camera.position = (5, 5, -15)
camera.look_at((5, 0, 0))

# Le convoyeur (simple rectangle gris)
convoyeur = Entity(model='cube', scale=(20, 1, 3), color=color.gray, position=(5, -1, 0))

# Le Capteur (une petite sphère qui changera de couleur)
capteur_visuel = Entity(model='sphere', scale=0.5, color=color.green, position=(8, 1, -2))
Text(text="CAPTEUR OPTIQUE", position=(-0.1, 0.4), scale=1)

# Liste pour gérer les bouteilles
bouteilles = []
vitesse_tapis = 4
en_bourrage = False

# Fonction pour faire apparaître des bouteilles
def spawn_bouteille():
    if not en_bourrage:
        bouteille = Entity(model='cube', color=color.cyan, scale=(0.8, 1.5, 0.8), position=(-5, 0.5, 0))
        bouteilles.append(bouteille)
    invoke(spawn_bouteille, delay=1.5) # Une nouvelle bouteille toutes les 1.5 sec

spawn_bouteille()

# --- LOGIQUE IA / DÉTECTION ---
status_text = Text(text="SYSTEME: NORMAL", position=(-0.65, 0.45), scale=1.5, color=color.green)

def update():
    global en_bourrage
    
    # Simulation du mouvement
    for b in bouteilles:
        # Si pas de bourrage, ça avance
        if not en_bourrage:
            b.x += time.dt * vitesse_tapis
        # Si bourrage, la bouteille qui a dépassé x=6 se bloque, les autres avancent jusqu'à la toucher
        else:
            if b.x < 6: 
                b.x += time.dt * vitesse_tapis
        
        # Nettoyage: si la bouteille sort de l'écran, on la supprime
        if b.x > 15:
            bouteilles.remove(b)
            destroy(b)

    # --- SIMULATION CAPTEUR ---
    # Si une bouteille reste trop longtemps devant le capteur (zone x entre 7 et 9)
    detection = False
    for b in bouteilles:
        if 7 < b.x < 9 and en_bourrage:
            detection = True
    
    if detection:
        capteur_visuel.color = color.red
        status_text.text = "ALERTE: BOURRAGE DETECTÉ !"
        status_text.color = color.red
    else:
        capteur_visuel.color = color.green
        status_text.text = "SYSTEME: NORMAL"
        status_text.color = color.green

# --- CONTRÔLES CLAVIER POUR LA DÉMO ---
def input(key):
    global en_bourrage
    if key == 'b': # Appuie sur B pour simuler la panne
        en_bourrage = not en_bourrage
        print(f"Simulation Bourrage: {en_bourrage}")

app.run()