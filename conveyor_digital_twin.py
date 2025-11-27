from ursina import *
import random

# --- CONFIGURATION & SETUP ---
app = Ursina()
window.title = "Digital Twin: Smart Conveyor System"
window.color = color.rgb(20, 20, 30) # Dark premium background
window.borderless = False
window.fullscreen = False

# Camera Setup
camera.position = (8, 10, -20)
camera.look_at((8, 0, 0))
EditorCamera() # Allow user to rotate around

# --- ASSETS & ENVIRONMENT ---

# 1. Factory Floor
floor = Entity(
    model='plane',
    scale=60,
    color=color.rgb(30, 30, 35),
    texture='white_cube',
    texture_scale=(60, 60),
    y=-2
)

# 2. Lighting
PointLight(parent=camera, position=(0, 10, -10), color=color.white)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# 3. The Conveyor Belt System
class ConveyorBelt(Entity):
    def __init__(self):
        super().__init__()
        # Main Structure
        self.body = Entity(parent=self, model='cube', scale=(30, 1, 4), color=color.rgb(50, 50, 60), position=(10, -1, 0))
        
        # Moving Belt Surface
        self.belt = Entity(parent=self, model='cube', scale=(30, 0.1, 3.2), color=color.rgb(20, 20, 20), position=(10, -0.45, 0))
        
        # Rails
        self.rail_front = Entity(parent=self, model='cube', scale=(30, 0.5, 0.2), color=color.rgb(200, 200, 0), position=(10, 0.5, -1.8))
        self.rail_back = Entity(parent=self, model='cube', scale=(30, 0.5, 0.2), color=color.rgb(200, 200, 0), position=(10, 0.5, 1.8))
        
        # Legs
        for x in [0, 10, 20]:
            Entity(parent=self, model='cube', scale=(1, 4, 3), color=color.rgb(40, 40, 50), position=(x, -3, 0))

conveyor = ConveyorBelt()

# 4. Sensors
# Optical Sensor (Arch)
sensor_arch = Entity(model='cube', scale=(0.5, 4, 5), color=color.dark_gray, position=(15, 1, 0))
sensor_laser = Entity(parent=sensor_arch, model='cube', scale=(0.1, 0.1, 0.9), color=color.red, y=0, alpha=0.6)
Text(text="OPTICAL", parent=sensor_arch, scale=2, y=0.6, x=-0.6, rotation_y=90)

# IoT Box (Vibration/Motor)
iot_box = Entity(model='cube', scale=(1.5, 2, 1.5), color=color.azure, position=(-2, 0, -2.5))
Text(text="IoT HUB", parent=iot_box, scale=2, y=0.6, x=-0.6, color=color.black)

# --- SIMULATION STATE ---
class SimulationState:
    def __init__(self):
        self.status = "NORMAL" # NORMAL, WEAR, JAM
        self.speed = 6.0
        self.vibration = 0.5
        self.current = 2.0
        self.bottle_count = 0
        self.last_spawn = 0

sim_state = SimulationState()

# --- BOTTLE LOGIC ---
bottles = []

class Bottle(Entity):
    def __init__(self):
        super().__init__(
            model='cylinder',
            color=color.rgba(0, 255, 255, 200),
            scale=(0.8, 2, 0.8),
            position=(-5, 0.5, random.uniform(-0.5, 0.5)),
            collider='box'
        )
        self.velocity = 0

    def update(self):
        # Movement Logic
        if sim_state.status == "JAM":
            # In a JAM, only move if not blocked by another bottle
            blocked = False
            hit_info = self.intersects()
            if hit_info.hit and hit_info.entity in bottles:
                # Simple check: if the bottle in front is stopped, I stop
                if hit_info.entity.x > self.x:
                    blocked = True
            
            if not blocked and self.x < 12: # Pile up at x=12
                 self.x += time.dt * sim_state.speed
        else:
            # Normal movement
            self.x += time.dt * sim_state.speed

        # Sensor Logic (Passing the arch)
        if 14.9 < self.x < 15.1:
            sensor_laser.color = color.green
            if not hasattr(self, 'counted'):
                sim_state.bottle_count += 1
                self.counted = True
        elif 15.1 < self.x < 15.3:
             sensor_laser.color = color.red

        # Cleanup
        if self.x > 25:
            bottles.remove(self)
            destroy(self)

def spawn_manager():
    if sim_state.status == "JAM":
        return # Don't spawn new bottles if jammed to avoid infinite pileup at start

    if time.time() - sim_state.last_spawn > 1.5: # Spawn every 1.5s
        b = Bottle()
        bottles.append(b)
        sim_state.last_spawn = time.time()

# --- DASHBOARD UI ---
class Dashboard(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.panel = Entity(parent=self, model='quad', scale=(0.4, 0.3), position=(0.65, 0.35), color=color.rgba(0, 0, 0, 180))
        
        self.title = Text(text="DIGITAL TWIN DASHBOARD", parent=self.panel, position=(-0.45, 0.4), scale=1.2, color=color.white)
        self.status_txt = Text(text="STATUS: NORMAL", parent=self.panel, position=(-0.45, 0.25), scale=1.5, color=color.green)
        
        self.vib_txt = Text(text="Vibration: 0.5 mm/s", parent=self.panel, position=(-0.45, 0.1), scale=1)
        self.cur_txt = Text(text="Current: 2.0 A", parent=self.panel, position=(-0.45, 0.0), scale=1)
        self.cnt_txt = Text(text="Bottles: 0", parent=self.panel, position=(-0.45, -0.1), scale=1)
        
        self.help_txt = Text(text="[1] NORMAL  [2] WEAR  [3] JAM", parent=self, position=(-0.85, -0.45), color=color.gray)

dashboard = Dashboard()

# --- MAIN LOOP ---
def update():
    spawn_manager()
    
    # Update Sensor Data based on State
    target_vib = 0.5
    target_cur = 2.0
    
    if sim_state.status == "NORMAL":
        sim_state.speed = 6.0
        target_vib = 0.5 + random.uniform(-0.1, 0.1)
        target_cur = 2.0 + random.uniform(-0.1, 0.1)
        dashboard.status_txt.text = "STATUS: NORMAL"
        dashboard.status_txt.color = color.green
        iot_box.color = color.azure
        
    elif sim_state.status == "WEAR":
        sim_state.speed = 5.5
        target_vib = 4.5 + random.uniform(-0.5, 0.5) # High vibration
        target_cur = 2.5 + random.uniform(-0.1, 0.1)
        dashboard.status_txt.text = "WARNING: BEARING WEAR"
        dashboard.status_txt.color = color.orange
        iot_box.color = color.orange
        # Visual shake effect
        iot_box.x = -2 + random.uniform(-0.05, 0.05)
        
    elif sim_state.status == "JAM":
        sim_state.speed = 0 # Belt stopped
        target_vib = 0.1 # No movement
        target_cur = 8.0 + random.uniform(-0.5, 0.5) # Stalled motor current spike
        dashboard.status_txt.text = "CRITICAL: JAM DETECTED"
        dashboard.status_txt.color = color.red
        iot_box.color = color.red

    # Smooth data transitions
    sim_state.vibration = lerp(sim_state.vibration, target_vib, time.dt * 5)
    sim_state.current = lerp(sim_state.current, target_cur, time.dt * 5)
    
    # Update UI
    dashboard.vib_txt.text = f"Vibration: {sim_state.vibration:.2f} mm/s"
    dashboard.cur_txt.text = f"Current: {sim_state.current:.2f} A"
    dashboard.cnt_txt.text = f"Bottles: {sim_state.bottle_count}"

# --- INPUTS ---
def input(key):
    if key == '1': sim_state.status = "NORMAL"
    if key == '2': sim_state.status = "WEAR"
    if key == '3': sim_state.status = "JAM"
    if key == 'escape': application.quit()

app.run()
