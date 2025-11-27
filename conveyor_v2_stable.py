from ursina import *
import random

# --- CONFIGURATION & SETUP ---
app = Ursina()
window.title = "Digital Twin: Industrial Conveyor V2"
window.color = color.rgb(25, 25, 30) # Dark industrial background
window.borderless = False

# Camera Setup
camera.position = (8, 12, -22)
camera.look_at((8, 0, 0))
EditorCamera()

# --- ASSETS & ENVIRONMENT ---

# 1. Factory Floor (Grid)
floor = Entity(
    model='plane',
    scale=80,
    color=color.rgb(40, 40, 45),
    texture='white_cube',
    texture_scale=(40, 40),
    y=-3
)

# 2. Lighting
PointLight(parent=camera, position=(0, 10, -10), color=color.white)
AmbientLight(color=color.rgba(120, 120, 120, 100))

# 3. The Conveyor Belt System (Aluminum Style)
class ConveyorBelt(Entity):
    def __init__(self):
        super().__init__()
        # Main Frame (Aluminum)
        self.frame = Entity(parent=self, model='cube', scale=(30, 1.5, 4), color=color.light_gray, position=(10, -1.5, 0))
        
        # Moving Belt Surface (Dark Rubber)
        self.belt = Entity(parent=self, model='cube', scale=(30, 0.2, 3.2), color=color.rgb(20, 20, 20), position=(10, -0.6, 0))
        
        # Side Rails (Safety)
        self.rail_front = Entity(parent=self, model='cube', scale=(30, 0.5, 0.2), color=color.rgb(200, 200, 200), position=(10, 0.5, -1.8))
        self.rail_back = Entity(parent=self, model='cube', scale=(30, 0.5, 0.2), color=color.rgb(200, 200, 200), position=(10, 0.5, 1.8))
        
        # Legs (Yellow Safety Color)
        for x in [0, 10, 20]:
            Entity(parent=self, model='cube', scale=(1, 4, 3.5), color=color.rgb(220, 180, 0), position=(x, -3.5, 0))

conveyor = ConveyorBelt()

# 4. Sensors
# Optical Sensor (Arch)
sensor_arch = Entity(model='cube', scale=(0.5, 4, 5), color=color.dark_gray, position=(15, 1, 0))
sensor_laser = Entity(parent=sensor_arch, model='cube', scale=(0.1, 0.1, 0.9), color=color.red, y=0, alpha=0.8)
Text(text="OPTICAL SENSOR", parent=sensor_arch, scale=2, y=0.6, x=-0.6, rotation_y=90)

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

# --- BOTTLE LOGIC (Composite Entity) ---
bottles = []

class Bottle(Entity):
    def __init__(self):
        super().__init__(position=(-5, 0.5, random.uniform(-0.5, 0.5)))
        
        # Visuals: Body + Cap (Using Cubes to avoid 'missing model' error)
        self.body = Entity(parent=self, model='cube', color=color.rgba(0, 200, 255, 220), scale=(0.8, 1.5, 0.8), y=0)
        self.cap = Entity(parent=self, model='cube', color=color.white, scale=(0.4, 0.3, 0.4), y=0.9)
        
        # Collider for logic
        self.collider = BoxCollider(self, center=(0,0,0), size=(0.8, 1.5, 0.8))
        self.velocity = 0

    def update(self):
        # Movement Logic
        if sim_state.status == "JAM":
            # In a JAM, check for collisions ahead
            blocked = False
            hit_info = self.intersects()
            if hit_info.hit:
                for entity in hit_info.entities:
                    # Check if we hit another bottle that is ahead of us
                    if entity in bottles and entity.x > self.x:
                        blocked = True
                        break
            
            # If not blocked and not at the jam point (x=12), move
            if not blocked and self.x < 12: 
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
        return # Don't spawn new bottles if jammed

    if time.time() - sim_state.last_spawn > 1.2: # Spawn every 1.2s
        b = Bottle()
        bottles.append(b)
        sim_state.last_spawn = time.time()

# --- DASHBOARD UI ---
class Dashboard(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.panel = Entity(parent=self, model='quad', scale=(0.5, 0.3), position=(0.60, 0.35), color=color.rgba(0, 0, 0, 200))
        
        self.title = Text(text="DIGITAL TWIN DASHBOARD", parent=self.panel, position=(-0.45, 0.4), scale=1.5, color=color.white)
        self.status_txt = Text(text="STATUS: NORMAL", parent=self.panel, position=(-0.45, 0.2), scale=2, color=color.green)
        
        self.vib_txt = Text(text="Vibration: 0.5 mm/s", parent=self.panel, position=(-0.45, 0.0), scale=1.2)
        self.cur_txt = Text(text="Current: 2.0 A", parent=self.panel, position=(-0.45, -0.15), scale=1.2)
        self.cnt_txt = Text(text="Bottles: 0", parent=self.panel, position=(-0.45, -0.3), scale=1.2)
        
        self.help_txt = Text(text="CONTROLS: [1] NORMAL  [2] WEAR  [3] JAM", parent=self, position=(-0.85, -0.45), color=color.gray)

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
