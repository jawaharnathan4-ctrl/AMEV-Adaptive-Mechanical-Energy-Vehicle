from ursina import *
from ursina.shaders import lit_with_shadows_shader
import math
import random
import time as clock

# ============================================================
# AMEV-SIM
# Adaptive Mechanical Energy Vehicle
# 3D Digital Twin + APERS + PRC + Flywheel + Energy Recovery
# ============================================================

app = Ursina()

window.title = "AMEV-SIM - 3D Digital Twin"
window.color = color.rgb(5, 8, 14)
window.fps_counter.enabled = False
window.exit_button.visible = False

# ============================================================
# COLORS
# ============================================================

CYAN   = color.rgb(40, 210, 255)
BLUE   = color.rgb(30, 100, 180)
GREEN  = color.rgb(60, 230, 130)
YELLOW = color.rgb(245, 210, 60)
ORANGE = color.rgb(255, 145, 40)
RED    = color.rgb(240, 60, 70)
WHITE  = color.rgb(235, 240, 245)
DARK   = color.rgb(12, 16, 22)
ROAD   = color.rgb(38, 43, 50)
METAL  = color.rgb(100, 110, 125)
GLASS  = color.rgb(20, 65, 90)

# ============================================================
# SIMULATION DATA
# ============================================================

pressure = 285.0
speed = 0.0
rpm = 500.0
air_flow = 0.0
temperature = 25.0
throttle = 0.0
brake = 0.0
steering = 0.0
road_slope = 4.0
vehicle_load = 1200.0

engine_output = 0.0
flywheel_energy = 0.0
braking_recovery = 0.0
exhaust_recovery = 0.0
wasted_energy = 0.0
energy_saved = 0.0
distance = 0.0

stage = 0
auto_demo = False
stage_timer = 0.0

# ============================================================
# HELPERS
# ============================================================

def clamp_value(v, a, b):
    return max(a, min(b, v))


def smooth(current, target, rate):
    return current + (target - current) * min(rate * time.dt, 1)


# ============================================================
# WORLD
# ============================================================

sun = DirectionalLight(shadows=True)
sun.rotation = (50, -35, 25)
sun.color = color.rgb(255, 245, 225)

ambient = AmbientLight()
ambient.color = color.rgba(100, 110, 125, 0.7)

Sky(color=color.rgb(8, 16, 28))

ground = Entity(
    model="plane",
    scale=180,
    texture="white_cube",
    texture_scale=(80, 80),
    color=color.rgb(25, 55, 40),
    shader=lit_with_shadows_shader
)

# ============================================================
# ROAD
# ============================================================

for i in range(45):

    z = i * 8 - 25

    y = 0.012 * max(0, i - 10) ** 2

    Entity(
        model="cube",
        scale=(9, 0.2, 8),
        position=(0, y, z),
        color=ROAD,
        shader=lit_with_shadows_shader
    )

    Entity(
        model="cube",
        scale=(0.15, 0.03, 3),
        position=(0, y + 0.12, z),
        color=WHITE
    )


# Road side poles

for side in (-1, 1):

    for i in range(30):

        z = i * 10

        Entity(
            model="cube",
            scale=(0.08, 0.7, 0.08),
            position=(side * 4.6, 0.35, z),
            color=WHITE,
            shader=lit_with_shadows_shader
        )


# Mountains

for i in range(15):

    x = -65 + i * 9
    h = random.uniform(6, 14)

    Entity(
        model="cube",
        scale=(10, h, 15),
        position=(x, h / 2, 55),
        rotation_y=random.uniform(-15, 15),
        color=color.rgb(20, 55, 55),
        shader=lit_with_shadows_shader
    )


# ============================================================
# AMEV VEHICLE
# ============================================================

car = Entity(position=(0, 0.65, 0))

# Chassis

Entity(
    parent=car,
    model="cube",
    scale=(3.3, 0.3, 6),
    color=DARK
)

# Main body

Entity(
    parent=car,
    model="cube",
    scale=(3, 0.85, 4.8),
    position=(0, 0.45, 0),
    color=CYAN,
    shader=lit_with_shadows_shader
)

# Lower body

Entity(
    parent=car,
    model="cube",
    scale=(3.2, 0.3, 5.2),
    position=(0, 0.18, 0),
    color=BLUE,
    shader=lit_with_shadows_shader
)

# Cabin

Entity(
    parent=car,
    model="cube",
    scale=(2.5, 0.9, 2.6),
    position=(0, 1.05, -0.2),
    color=GLASS,
    shader=lit_with_shadows_shader
)

# Roof

Entity(
    parent=car,
    model="cube",
    scale=(2.35, 0.12, 2.5),
    position=(0, 1.55, -0.2),
    color=BLUE
)

# Hood

Entity(
    parent=car,
    model="cube",
    scale=(2.65, 0.2, 1),
    position=(0, 0.9, 2.2),
    color=CYAN
)

# Headlights

for x in (-0.9, 0.9):

    Entity(
        parent=car,
        model="cube",
        scale=(0.5, 0.2, 0.12),
        position=(x, 0.85, 2.72),
        color=color.rgb(220, 250, 255)
    )

# ============================================================
# WHEELS
# ============================================================

wheels = []

for x in (-1.6, 1.6):

    for z in (-1.95, 1.95):

        wheel = Entity(
            parent=car,
            model="cylinder",
            scale=(0.8, 0.35, 0.8),
            position=(x, 0.12, z),
            rotation=(0, 0, 90),
            color=DARK,
            shader=lit_with_shadows_shader
        )

        Entity(
            parent=wheel,
            model="cylinder",
            scale=0.4,
            rotation=(0, 0, 90),
            color=METAL
        )

        wheels.append(wheel)


# ============================================================
# COMPRESSED AIR TANK
# ============================================================

tank = Entity(
    parent=car,
    model="cylinder",
    scale=(1.3, 2.1, 1.3),
    position=(0, 1.05, -1.15),
    rotation=(0, 0, 90),
    color=METAL,
    shader=lit_with_shadows_shader
)

Entity(
    parent=tank,
    model="cylinder",
    scale=(1.35, 0.12, 1.35),
    position=(0, 0.3, 0),
    rotation=(0, 0, 90),
    color=CYAN
)

tank_light = Entity(
    parent=car,
    model="sphere",
    scale=0.2,
    position=(0, 1.05, -1.15),
    color=CYAN
)

# ============================================================
# PNEUMATIC ENGINE
# ============================================================

engine = Entity(
    parent=car,
    model="cube",
    scale=(1.5, 0.8, 1.1),
    position=(0, 0.75, 1.0),
    color=METAL,
    shader=lit_with_shadows_shader
)

for x in (-0.5, 0, 0.5):

    Entity(
        parent=engine,
        model="cylinder",
        scale=(0.25, 0.65, 0.25),
        position=(x, 0.45, 0),
        color=METAL
    )

engine_light = Entity(
    parent=car,
    model="sphere",
    scale=0.18,
    position=(0, 1.0, 1.0),
    color=ORANGE
)

# ============================================================
# FLYWHEEL
# ============================================================

flywheel = Entity(
    parent=car,
    model="cylinder",
    scale=(1.15, 0.35, 1.15),
    position=(0, 0.95, 0.25),
    rotation=(0, 0, 90),
    color=YELLOW,
    shader=lit_with_shadows_shader
)

Entity(
    parent=flywheel,
    model="cylinder",
    scale=0.65,
    rotation=(0, 0, 90),
    color=DARK
)

# ============================================================
# APERS
# ============================================================

apers = Entity(
    parent=car,
    model="cube",
    scale=(1.3, 0.6, 1.0),
    position=(0, 0.65, -0.15),
    color=GREEN,
    shader=lit_with_shadows_shader
)

apers_light = Entity(
    parent=car,
    model="sphere",
    scale=0.18,
    position=(0, 0.95, -0.15),
    color=GREEN
)

# ============================================================
# PRC
# ============================================================

prc = Entity(
    parent=car,
    model="cube",
    scale=(1.05, 0.5, 0.85),
    position=(0, 0.65, -0.75),
    color=CYAN,
    shader=lit_with_shadows_shader
)

# ============================================================
# EXHAUST
# ============================================================

Entity(
    parent=car,
    model="cylinder",
    scale=(0.13, 1.4, 0.13),
    position=(1.25, 0.7, -2.4),
    rotation=(90, 0, 0),
    color=METAL
)

# ============================================================
# ENERGY PARTICLES
# ============================================================

particles = []

for i in range(35):

    p = Entity(
        model="sphere",
        scale=0.08,
        position=(
            random.uniform(-0.5, 0.5),
            random.uniform(0.6, 1.2),
            random.uniform(-2, 2)
        ),
        color=CYAN
    )

    particles.append(p)


# ============================================================
# STAGES
# ============================================================

stages = [

    ("SYSTEM INITIALIZATION",
     "AMEV digital twin is initializing."),

    ("COMPRESSED AIR TANK",
     "High pressure pneumatic energy is stored in the tank."),

    ("ADAPTIVE PRESSURE CONTROL",
     "Pressure controller adjusts air demand according to load."),

    ("PNEUMATIC ENGINE",
     "Compressed air is converted into mechanical output."),

    ("VEHICLE MOTION",
     "Mechanical output is transferred to the vehicle wheels."),

    ("EXHAUST AIR",
     "Exhaust air is redirected toward the recovery system."),

    ("APERS",
     "Adaptive Pressure and Energy Recovery System is activated."),

    ("PRC",
     "Pressure Recovery Chamber buffers recoverable pneumatic energy."),

    ("FLYWHEEL RECOVERY",
     "Braking energy is stored mechanically in the flywheel."),

    ("AI ENERGY MANAGEMENT",
     "Adaptive controller selects the most efficient operating mode."),

    ("BRAKING RECOVERY",
     "Vehicle braking is converted into recoverable mechanical energy."),

    ("SECONDARY WORK",
     "Recovered energy can support a secondary pneumatic load."),

    ("ENERGY WASTE ANALYZER",
     "Useful energy and wasted energy are compared."),

    ("DIGITAL TWIN RESPONSE",
     "The virtual vehicle responds to changing driving conditions."),

    ("FULL SYSTEM RUN",
     "All AMEV subsystems are now operating together."),

    ("SIMULATION COMPLETE",
     "AMEV simulation completed. Values are model outputs.")
]


# ============================================================
# UI
# ============================================================

title = Text(
    "AMEV-SIM  |  3D DIGITAL TWIN",
    x=-0.47,
    y=0.46,
    scale=1.3,
    color=CYAN
)

subtitle = Text(
    "ADAPTIVE MECHANICAL ENERGY VEHICLE",
    x=-0.47,
    y=0.415,
    scale=0.7,
    color=WHITE
)

stage_title = Text(
    "STAGE 01",
    x=-0.47,
    y=0.36,
    scale=1,
    color=YELLOW
)

stage_info = Text(
    "SYSTEM INITIALIZATION",
    x=-0.47,
    y=0.32,
    scale=0.7,
    color=WHITE
)

stats = Text(
    "",
    x=0.30,
    y=0.40,
    scale=0.68,
    color=WHITE
)

energy_flow = Text(
    "",
    x=-0.47,
    y=-0.25,
    scale=0.65,
    color=GREEN
)

warning = Text(
    "",
    x=-0.47,
    y=-0.43,
    scale=0.6,
    color=ORANGE
)

controls = Text(
    "SPACE NEXT STAGE | ENTER AUTO DEMO | W ACCELERATE | S BRAKE | A/D STEER | R RESET",
    origin=(0, 0),
    y=-0.48,
    scale=0.55,
    color=color.rgb(170, 180, 195)
)

# ============================================================
# CAMERA
# ============================================================

camera.position = (10, 5.5, -12)
camera.look_at(car)


def cinematic_camera():

    t = clock.time()

    if stage in (1, 2):

        target = Vec3(7, 3.5, -7)

    elif stage in (3, 4):

        target = Vec3(-7, 3.2, 3)

    elif stage in (6, 7):

        target = Vec3(5, 2.7, -2)

    elif stage in (8, 10):

        target = Vec3(-6, 2.7, -3)

    else:

        target = Vec3(
            math.sin(t * 0.15) * 10,
            4.5,
            -11 + math.cos(t * 0.15) * 3
        )

    camera.position = lerp(
        camera.position,
        target,
        time.dt * 1.5
    )

    camera.look_at(car)


# ============================================================
# STAGE CONTROL
# ============================================================

def set_stage(number):

    global stage

    stage = number % len(stages)

    name, description = stages[stage]

    stage_title.text = "STAGE %02d" % (stage + 1)

    stage_info.text = (
        name +
        "\n" +
        description
    )


def next_stage():

    set_stage(stage + 1)


# ============================================================
# AUTO DEMO
# ============================================================

def demo_condition():

    if stage == 0:
        throttle = 0
        brake = 0
        road_slope = 2

    elif stage == 1:
        throttle = 0.15
        brake = 0
        road_slope = 2

    elif stage == 2:
        throttle = 0.30
        brake = 0
        road_slope = 8

    elif stage == 3:
        throttle = 0.65
        brake = 0
        road_slope = 4

    elif stage == 4:
        throttle = 0.85
        brake = 0
        road_slope = 6

    elif stage == 5:
        throttle = 0.50
        brake = 0
        road_slope = 3

    elif stage == 6:
        throttle = 0.35
        brake = 0
        road_slope = 5

    elif stage == 7:
        throttle = 0.25
        brake = 0
        road_slope = 4

    elif stage == 8:
        throttle = 0
        brake = 0.85
        road_slope = -3

    elif stage == 9:
        throttle = 0.30
        brake = 0
        road_slope = 1

    elif stage == 10:
        throttle = 0
        brake = 0.90
        road_slope = -5

    elif stage == 11:
        throttle = 0.20
        brake = 0
        road_slope = -2

    elif stage == 12:
        throttle = 0.30
        brake = 0
        road_slope = 2

    elif stage == 13:
        throttle = 0.55
        brake = 0
        road_slope = 7

    elif stage == 14:
        throttle = 0.75
        brake = 0
        road_slope = 4

    else:
        throttle = 0
        brake = 0.2
        road_slope = 0

    return throttle, brake, road_slope


# ============================================================
# PHYSICS
# ============================================================

def simulate():

    global pressure
    global speed
    global rpm
    global air_flow
    global engine_output
    global flywheel_energy
    global braking_recovery
    global exhaust_recovery
    global wasted_energy
    global energy_saved
    global distance
    global temperature

    # Air consumption

    air_flow = (
        0.018 +
        throttle * 0.105
    )

    air_flow *= (
        1 +
        max(0, road_slope) * 0.018
    )

    air_flow *= (
        1 +
        max(0, vehicle_load - 1000) / 12000
    )

    air_flow = clamp_value(
        air_flow,
        0,
        0.18
    )

    # Pneumatic engine

    engine_output = (
        air_flow *
        pressure *
        0.16
    )

    # Vehicle physics

    drive_force = throttle * (
        1 +
        pressure / 300
    )

    resistance = (
        0.018 +
        abs(road_slope) * 0.006 +
        vehicle_load / 65000
    )

    brake_force = brake * 0.22

    acceleration = (
        drive_force -
        resistance -
        brake_force
    )

    # Downhill assist

    if road_slope < 0:

        acceleration += (
            abs(road_slope) *
            0.012
        )

    speed += (
        acceleration *
        22 *
        time.dt
    )

    speed = clamp_value(
        speed,
        0,
        130
    )

    # Tank pressure

    pressure -= (
        air_flow *
        (0.38 + throttle * 0.75) *
        time.dt *
        2.8
    )

    pressure = clamp_value(
        pressure,
        35,
        300
    )

    # ========================================================
    # BRAKING RECOVERY
    # ========================================================

    recovery = (
        brake *
        max(speed, 1) *
        0.008
    )

    recovery *= (
        0.55 +
        max(0, road_slope) * 0.02
    )

    braking_recovery += (
        recovery *
        time.dt
    )

    flywheel_energy += (
        recovery *
        time.dt *
        0.75
    )

    # ========================================================
    # FLYWHEEL ASSIST
    # ========================================================

    if (
        throttle > 0.15 and
        flywheel_energy > 0.2
    ):

        assist = min(
            flywheel_energy,
            throttle * 0.8 * time.dt
        )

        flywheel_energy -= assist

        engine_output += (
            assist * 0.5
        )

    # ========================================================
    # APERS / PRC RECOVERY
    # ========================================================

    exhaust_available = (
        air_flow *
        pressure *
        0.055
    )

    recovery_efficiency = 0.08

    if stage >= 6:
        recovery_efficiency = 0.18

    if stage >= 8:
        recovery_efficiency = 0.28

    if stage >= 12:
        recovery_efficiency = 0.34

    exhaust_recovery += (
        exhaust_available *
        recovery_efficiency *
        time.dt
    )

    # ========================================================
    # ENERGY WASTE
    # ========================================================

    useful_energy = (
        engine_output *
        time.dt
    )

    recovered_energy = (
        recovery +
        exhaust_available *
        recovery_efficiency
    ) * time.dt

    waste = max(
        0,
        useful_energy * 0.65 -
        recovered_energy
    )

    wasted_energy += waste

    baseline = (
        useful_energy *
        0.75 +
        0.0001
    )

    energy_saved = clamp_value(
        (
            recovered_energy /
            baseline
        ) * 100,
        0,
        99
    )

    # Range

    if air_flow > 0.002:

        range_value = (
            pressure /
            max(
                air_flow * 0.78,
                0.001
            )
        )

    else:

        range_value = 500

    # RPM

    rpm = (
        500 +
        speed * 42 +
        throttle * 1500 +
        flywheel_energy * 30
    )

    rpm = clamp_value(
        rpm,
        500,
        6500
    )

    # Temperature

    temperature += (
        throttle * 0.8 -
        (temperature - 25) * 0.03
    ) * time.dt

    # Distance

    distance += (
        speed *
        time.dt /
        3.6
    )

    return range_value


# ============================================================
# HUD
# ============================================================

def update_hud(range_value):

    global warning

    stats.text = (
        "TANK PRESSURE     %6.1f bar\n"
        "VEHICLE SPEED     %6.1f km/h\n"
        "AIR FLOW          %6.3f kg/s\n"
        "FLYWHEEL RPM      %6.0f rpm\n"
        "ESTIMATED RANGE   %6.1f km\n"
        "ENGINE OUTPUT     %6.2f kW\n"
        "TEMPERATURE       %6.1f C\n"
        "VEHICLE LOAD      %6.0f kg\n"
        "ROAD SLOPE        %6.1f %%\n"
        "FLYWHEEL ENERGY   %6.2f\n"
        "BRAKE RECOVERY    %6.2f\n"
        "EXHAUST RECOVERY  %6.2f"
        % (
            pressure,
            speed,
            air_flow,
            rpm,
            range_value,
            engine_output,
            temperature,
            vehicle_load,
            road_slope,
            flywheel_energy,
            braking_recovery,
            exhaust_recovery
        )
    )

    energy_flow.text = (
        "LIVE ENERGY FLOW\n\n"
        "COMPRESSED AIR TANK\n"
        "          |\n"
        "          v\n"
        "PNEUMATIC ENGINE\n"
        "          |\n"
        "          v\n"
        "VEHICLE MOTION\n"
        "          |\n"
        "          v\n"
        "EXHAUST AIR\n"
        "          |\n"
        "          v\n"
        "APERS / PRC\n"
        "       /     \\\n"
        "      v       v\n"
        "   BUFFER   FLYWHEEL\n\n"
        "ENERGY SAVED: %.2f %%\n"
        "WASTED ENERGY: %.2f kJ"
        % (
            energy_saved,
            wasted_energy
        )
    )

    if pressure < 80:

        warning.text = (
            "AI ALERT: LOW PRESSURE - "
            "REDUCING UNNECESSARY AIR DEMAND"
        )

        warning.color = RED

    elif brake > 0.3:

        warning.text = (
            "RECOVERY MODE: "
            "BRAKING ENERGY -> FLYWHEEL -> PRC"
        )

        warning.color = GREEN

    elif road_slope > 6:

        warning.text = (
            "AI MODE: UPHILL / HIGH LOAD - "
            "OPTIMIZING PRESSURE"
        )

        warning.color = ORANGE

    else:

        warning.text = (
            "MODEL OUTPUT ONLY - "
            "NOT MEASURED REAL WORLD PERFORMANCE"
        )

        warning.color = WHITE


# ============================================================
# RESET
# ============================================================

def reset_sim():

    global pressure
    global speed
    global rpm
    global throttle
    global brake
    global steering
    global road_slope
    global flywheel_energy
    global braking_recovery
    global exhaust_recovery
    global wasted_energy
    global energy_saved
    global distance

    pressure = 285
    speed = 0
    rpm = 500
    throttle = 0
    brake = 0
    steering = 0
    road_slope = 4
    flywheel_energy = 0
    braking_recovery = 0
    exhaust_recovery = 0
    wasted_energy = 0
    energy_saved = 0
    distance = 0

    car.position = Vec3(0, 0.65, 0)
    car.rotation_y = 0

    set_stage(0)


# ============================================================
# KEYBOARD
# ============================================================

def input(key):

    global auto_demo

    if key == "space":

        auto_demo = False
        next_stage()

    if key == "enter":

        auto_demo = not auto_demo

    if key == "r":

        auto_demo = False
        reset_sim()

    if key == "escape":

        application.quit()


# ============================================================
# MAIN UPDATE
# ============================================================

def update():

    global throttle
    global brake
    global steering
    global road_slope
    global stage_timer

    # ========================================================
    # MANUAL CONTROL
    # ========================================================

    if not auto_demo:

        throttle = smooth(
            throttle,
            1 if held_keys["w"] else 0,
            5
        )

        brake = smooth(
            brake,
            1 if held_keys["s"] else 0,
            7
        )

        steering_target = 0

        if held_keys["a"]:
            steering_target = -1

        if held_keys["d"]:
            steering_target = 1

        steering = smooth(
            steering,
            steering_target,
            8
        )

    # ========================================================
    # AUTOMATIC DEMO
    # ========================================================

    if auto_demo:

        stage_timer += time.dt

        values = demo_condition()

        throttle = values[0]
        brake = values[1]
        road_slope = values[2]

        if stage_timer > 5:

            stage_timer = 0

            next_stage()

    # ========================================================
    # SIMULATION
    # ========================================================

    range_value = simulate()

    # ========================================================
    # VEHICLE MOTION
    # ========================================================

    car.rotation_y = smooth(
        car.rotation_y,
        steering * 9,
        4
    )

    car.y = (
        0.65 +
        math.sin(clock.time() * 3) * 0.008
    )

    # Wheel rotation

    for wheel in wheels:

        wheel.rotation_x += (
            speed *
            18 *
            time.dt
        )

    # Flywheel rotation

    flywheel.rotation_y += (
        rpm *
        0.07 *
        time.dt
    )

    # ========================================================
    # ENERGY PARTICLES
    # ========================================================

    for p in particles:

        p.z += (
            2 +
            speed * 0.025
        ) * time.dt

        if p.z > 3:

            p.z = -2.5

            p.x = random.uniform(
                -0.5,
                0.5
            )

            p.y = random.uniform(
                0.65,
                1.2
            )

        if stage in (6, 7, 11, 12):

            p.color = GREEN

        elif stage in (8, 10):

            p.color = YELLOW

        else:

            p.color = CYAN

    # ========================================================
    # COMPONENT LIGHTS
    # ========================================================

    pulse = (
        1 +
        math.sin(clock.time() * 5) *
        0.15
    )

    tank_light.scale = 0.2 * pulse
    engine_light.scale = 0.18 * pulse
    apers_light.scale = 0.18 * pulse

    if pressure < 80:

        tank_light.color = RED

    else:

        tank_light.color = CYAN

    if throttle > 0.1:

        engine_light.color = ORANGE

    else:

        engine_light.color = METAL

    if stage >= 6:

        apers_light.color = GREEN

    # ========================================================
    # CAMERA
    # ========================================================

    cinematic_camera()

    # ========================================================
    # HUD
    # ========================================================

    update_hud(range_value)


# ============================================================
# START
# ============================================================

reset_sim()

print("")
print("==============================================")
print(" AMEV-SIM 3D DIGITAL TWIN")
print("==============================================")
print("SPACE  = Next stage")
print("ENTER  = Automatic demo")
print("W      = Accelerate")
print("S      = Brake / recovery")
print("A/D    = Steering")
print("R      = Reset")
print("ESC    = Exit")
print("==============================================")

app.run()