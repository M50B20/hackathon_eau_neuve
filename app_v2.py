from ursina import *
import random

app = Ursina()
window.title = "Simulateur Supervision Convoyeur - Hackathon 2025"
window.color = color.black

# --- CONFIGURATION CAMÉRA ---
camera.position = (5, 7, -18)
camera.rotation_x = 20
camera.look_at((5, 0, 0))

# --- VARIABLES SYSTÈME (Données Capteurs) ---
sys_state = "NORMAL" # NORMAL, USURE, BOURRAGE
motor_speed = 5
vibration_level = 1.0 # En mm/s
motor_amps = 2.5 # En Ampères
bouteilles_count = 0

# --- DÉCORS ET MÉCANIQUE ---
# Le sol
Entity(model='plane', scale=50, color=color.dark_gray, y=-2, texture='white_cube')

# Le Convoyeur (Structure métal)
convoyeur_body = Entity(model='cube', scale=(24, 1, 4), color=color.gray, position=(5, -1, 0))
tapis = Entity(model='cube', scale=(24, 0.1, 3), color=color.black, position=(5, -0.45, 0))

# Rails de guidage (Partie Conception Mécanique)
rail_front = Entity(model='cube', scale=(24, 0.5, 0.1), color=color.light_gray, position=(5, 0.5, -1.6))
rail_back = Entity(model='cube', scale=(24, 0.5, 0.1), color=color.light_gray, position=(5, 0.5, 1.6))

# --- CAPTEURS VISUELS ---
# 1. Capteur Optique (Arche au dessus du tapis)
arche = Entity(model='cube', scale=(0.5, 3, 4.5), color=color.dark_gray, position=(8, 1, 0))
laser_beam = Entity(model='cube', scale=(0.1, 0.1, 4), color=color.red, position=(8, 1, 0), alpha=0.5)
Text(text="CPT. OPTIQUE", position=(0.25, 0.2), scale=0.8, color=color.white)

# 2. Capteur Vibration/Moteur (Boitier sur le côté)
motor_box = Entity(model='cube', scale=(2, 2, 2), color=color.azure, position=(-6, 0, -2.5))
Text(text="MOTEUR + VIBRATION", position=(-0.6, 0.1), scale=0.8, color=color.white)

# --- INTERFACE HOMME-MACHINE (DASHBOARD) ---
# Panneau de fond
Entity(parent=camera.ui, model='quad', scale=(0.5, 0.4), position=(0.6, 0.25), color=color.dark_gray, alpha=0.8)

txt_titre = Text(text="SUPERVISION IA", position=(0.45, 0.42), scale=1.5, color=color.white)
txt_etat = Text(text="ÉTAT: NORMAL", position=(0.40, 0.35), scale=1.2, color=color.green)
txt_vibe = Text(text="Vibration: 1.2 mm/s", position=(0.40, 0.28), scale=1)
txt_amps = Text(text="Conso Moteur: 2.5 A", position=(0.40, 0.23), scale=1)
txt_cnt = Text(text="Prod: 0 Bouteilles", position=(0.40, 0.18), scale=1)

# --- LOGIQUE BOUTEILLES ---
bouteilles = []
def spawn_bouteille():
    if sys_state != "BOURRAGE":
        # Bouteille d'eau un peu transparente
        b = Entity(model='cube', color=color.rgba(0, 255, 255, 200), scale=(0.6, 1.5, 0.6), position=(-8, 0.4, 0))
        bouteilles.append(b)
        # Randomise un peu l'espacement pour faire réaliste
        invoke(spawn_bouteille, delay=random.uniform(1.2, 1.8))

spawn_bouteille()

def update():
    global vibration_level, motor_amps, bouteilles_count, motor_speed
    
    # 1. SIMULATION DES DONNÉES CAPTEURS SELON L'ÉTAT
    if sys_state == "NORMAL":
        target_vibe = 1.0 + random.uniform(-0.1, 0.1)
        target_amps = 2.5 + random.uniform(-0.1, 0.1)
        motor_speed = 6
        txt_etat.text = "ÉTAT: OPTIMAL"
        txt_etat.color = color.green
        motor_box.color = color.azure
        
    elif sys_state == "USURE":
        # Vibration augmente, Ampérage normal
        target_vibe = 4.5 + random.uniform(-0.5, 0.5) # HAUTE VIBRATION
        target_amps = 2.8 + random.uniform(-0.1, 0.1)
        motor_speed = 6
        txt_etat.text = "ALERTE: DÉSYNCHRO (IA PREDICT)"
        txt_etat.color = color.orange
        # Effet visuel: le moteur secoue
        motor_box.x = -6 + random.uniform(-0.05, 0.05)
        
    elif sys_state == "BOURRAGE":
        # Moteur force (Ampérage haut), Vitesse nulle
        target_vibe = 0.2 # Plus de vibration car à l'arrêt
        target_amps = 8.5 + random.uniform(-0.5, 0.5) # PIC D'INTENSITÉ
        motor_speed = 0
        txt_etat.text = "STOP: BOURRAGE DÉTECTÉ"
        txt_etat.color = color.red
        motor_box.color = color.red

    # Lissage des valeurs pour l'affichage (Lerp)
    vibration_level = lerp(vibration_level, target_vibe, time.dt * 2)
    motor_amps = lerp(motor_amps, target_amps, time.dt * 2)

    # Mise à jour Textes
    txt_vibe.text = f"Vibration: {vibration_level:.2f} mm/s"
    txt_amps.text = f"Conso Moteur: {motor_amps:.2f} A"
    
    # 2. PHYSIQUE DU CONVOYEUR
    for b in bouteilles:
        # Avance
        if b.x < 7 or sys_state != "BOURRAGE":
             b.x += time.dt * motor_speed
        
        # Simulation bourrage physique : les bouteilles s'empilent
        if sys_state == "BOURRAGE" and b.x >= 6:
            # Elles tremblent un peu car elles sont coincées
            b.x += random.uniform(-0.01, 0.01)

        # Détection passage capteur optique
        if 7.9 < b.x < 8.1 and motor_speed > 0:
            laser_beam.color = color.green # Flash vert
        else:
            laser_beam.color = color.red

        # Nettoyage
        if b.x > 15:
            bouteilles.remove(b)
            destroy(b)
            if sys_state != "BOURRAGE":
                bouteilles_count += 1
                txt_cnt.text = f"Prod: {bouteilles_count} Bouteilles"

# --- CONTRÔLES DÉMO ---
def input(key):
    global sys_state
    if key == '1': sys_state = "NORMAL"
    if key == '2': sys_state = "USURE"
    if key == '3': sys_state = "BOURRAGE"

# Instructions à l'écran
Text(text="CONTROLES: [1] Normal  [2] Désynchro/Usure  [3] Bourrage", position=(-0.5, -0.45), color=color.gray)

app.run()