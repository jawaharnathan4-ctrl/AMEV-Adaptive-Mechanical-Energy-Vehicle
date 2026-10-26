"""
AMEV-SIM
Adaptive Mechanical Energy Vehicle
Intelligent Simulation & Energy Management Platform

Single-file prototype.
No external Python packages required.

Run:
    python amev_sim.py

Then open:
    http://localhost:8000
"""

import json
import math
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs


# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 8000

# Approximate prototype parameters.
# These are MODEL PARAMETERS, not measured real-world values.

ATM_PRESSURE_BAR = 1.013

TANK_VOLUME_M3 = 0.12
TANK_MAX_PRESSURE_BAR = 300.0

VEHICLE_MASS_KG = 850.0
WHEEL_RADIUS_M = 0.28

AIR_DENSITY_KG_M3 = 1.225

FLYWHEEL_INERTIA = 0.18
FLYWHEEL_MAX_RPM = 5000.0
FLYWHEEL_MIN_RPM = 500.0

ROLLING_COEFF = 0.015
DRAG_COEFF = 0.32
FRONTAL_AREA = 2.0

GRAVITY = 9.81

# ============================================================
# GLOBAL SIMULATION STATE
# ============================================================

state_lock = threading.Lock()

state = {
    "tank_pressure": 285.0,
    "speed": 42.0,
    "mass": 850.0,
    "slope": 0.0,
    "temperature": 25.0,
    "flywheel_rpm": 1850.0,

    "throttle": 0.0,
    "brake": 0.0,
    "steering": 0.0,

    "air_flow": 0.0,
    "pressure_drop": 0.0,
    "engine_power_kw": 0.0,

    "flywheel_energy_kj": 0.0,
    "braking_recovery_kj": 0.0,
    "exhaust_recovery_kj": 0.0,

    "total_energy_used_kj": 0.0,
    "total_energy_recovered_kj": 0.0,
    "baseline_energy_loss_kj": 0.0,

    "distance_km": 0.0,
    "range_km": 0.0,

    "efficiency": 0.0,
    "recovery_percent": 0.0,
    "energy_saved_percent": 0.0,
    "exhaust_utilized_percent": 0.0,

    "ai_mode": "IDLE",
    "ai_message": "System ready",

    "energy_available_kj": 0.0,
    "useful_energy_kj": 0.0,
    "wasted_energy_kj": 0.0,

    "scenario": "CRUISE",

    "last_update": time.time()
}


# ============================================================
# PHYSICS / ENERGY FUNCTIONS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def air_energy_from_pressure(pressure_bar):
    """
    Simplified compressed-air stored-energy approximation.

    This is intentionally a simplified simulation model.
    It should not be treated as a thermodynamic certification model.
    """

    absolute_bar = max(pressure_bar + ATM_PRESSURE_BAR, 1.0)

    # Simplified relative energy model.
    energy_mj = (
        TANK_VOLUME_M3
        * 1_000_000
        * math.log(absolute_bar / ATM_PRESSURE_BAR)
        * 0.25
    )

    return max(energy_mj, 0.0)


def flywheel_energy_kj(rpm):
    """
    Rotational kinetic energy:
        E = 1/2 * I * omega^2
    """

    omega = rpm * 2.0 * math.pi / 60.0

    energy_j = 0.5 * FLYWHEEL_INERTIA * omega * omega

    return energy_j / 1000.0


def aerodynamic_force(speed_ms):
    return (
        0.5
        * AIR_DENSITY_KG_M3
        * DRAG_COEFF
        * FRONTAL_AREA
        * speed_ms ** 2
    )


def rolling_force():
    return VEHICLE_MASS_KG * GRAVITY * ROLLING_COEFF


def slope_force(slope_percent):
    angle = math.atan(slope_percent / 100.0)
    return VEHICLE_MASS_KG * GRAVITY * math.sin(angle)


def calculate_engine_power(pressure_bar, throttle):
    """
    Simplified pneumatic engine model.
    """

    pressure_factor = clamp(
        (pressure_bar - 40.0) / 260.0,
        0.0,
        1.0
    )

    base_power_kw = 18.0 * pressure_factor

    return base_power_kw * throttle


def calculate_air_flow(pressure_bar, throttle):
    """
    Simplified air consumption model.
    """

    pressure_factor = clamp(
        pressure_bar / TANK_MAX_PRESSURE_BAR,
        0.0,
        1.0
    )

    flow = (
        0.025
        + throttle * 0.28
        + pressure_factor * throttle * 0.12
    )

    return flow


# ============================================================
# ADAPTIVE ENERGY MANAGEMENT
# ============================================================

def adaptive_energy_manager():
    """
    Rule-based AI-style adaptive controller.

    Later this can be replaced with an actual ML model
    without changing the dashboard.
    """

    pressure = state["tank_pressure"]
    speed = state["speed"]
    slope = state["slope"]
    brake = state["brake"]
    throttle = state["throttle"]
    rpm = state["flywheel_rpm"]

    if pressure < 70:
        return {
            "mode": "LOW PRESSURE",
            "air_multiplier": 0.55,
            "flywheel_assist": True,
            "recovery": 0.70,
            "message": "Tank pressure low → reducing unnecessary air consumption"
        }

    if brake > 0.2:
        return {
            "mode": "BRAKING RECOVERY",
            "air_multiplier": 0.25,
            "flywheel_assist": False,
            "recovery": 0.95,
            "message": "Braking detected → maximizing flywheel recovery"
        }

    if slope < -3 and speed > 20:
        return {
            "mode": "DOWNHILL RECOVERY",
            "air_multiplier": 0.35,
            "flywheel_assist": False,
            "recovery": 0.90,
            "message": "Downhill detected → prioritizing energy recovery"
        }

    if slope > 5 and throttle > 0.4:
        return {
            "mode": "UPHILL ASSIST",
            "air_multiplier": 1.10,
            "flywheel_assist": True,
            "recovery": 0.35,
            "message": "Uphill demand → providing adaptive pneumatic assistance"
        }

    if throttle > 0.75:
        return {
            "mode": "HIGH POWER",
            "air_multiplier": 1.0,
            "flywheel_assist": True,
            "recovery": 0.40,
            "message": "High acceleration demand → optimized power delivery"
        }

    if rpm > 4300:
        return {
            "mode": "FLYWHEEL PROTECTION",
            "air_multiplier": 0.75,
            "flywheel_assist": False,
            "recovery": 0.85,
            "message": "Flywheel RPM high → limiting additional recovery"
        }

    return {
        "mode": "ECO CRUISE",
        "air_multiplier": 0.72,
        "flywheel_assist": True,
        "recovery": 0.50,
        "message": "Cruising → optimizing energy consumption"
    }


# ============================================================
# SIMULATION STEP
# ============================================================

def simulation_step(dt=0.2):

    with state_lock:

        ai = adaptive_energy_manager()

        state["ai_mode"] = ai["mode"]
        state["ai_message"] = ai["message"]

        throttle = state["throttle"]
        brake = state["brake"]

        speed_ms = state["speed"] / 3.6

        # ----------------------------------------------------
        # Forces
        # ----------------------------------------------------

        aero = aerodynamic_force(speed_ms)
        rolling = rolling_force()
        slope = slope_force(state["slope"])

        engine_power_kw = calculate_engine_power(
            state["tank_pressure"],
            throttle
        )

        engine_force = (
            engine_power_kw * 1000.0 / max(speed_ms, 1.0)
        )

        brake_force = (
            brake
            * VEHICLE_MASS_KG
            * GRAVITY
            * 0.45
        )

        net_force = (
            engine_force
            - aero
            - rolling
            - slope
            - brake_force
        )

        acceleration = net_force / max(state["mass"], 1.0)

        # ----------------------------------------------------
        # Speed update
        # ----------------------------------------------------

        state["speed"] += acceleration * dt * 3.6

        state["speed"] = clamp(
            state["speed"],
            0.0,
            120.0
        )

        # ----------------------------------------------------
        # Air consumption
        # ----------------------------------------------------

        raw_air_flow = calculate_air_flow(
            state["tank_pressure"],
            throttle
        )

        state["air_flow"] = (
            raw_air_flow
            * ai["air_multiplier"]
        )

        # Pressure drop model
        pressure_drop = (
            state["air_flow"]
            * dt
            * 8.0
        )

        pressure_drop = clamp(
            pressure_drop,
            0.0,
            3.0
        )

        state["pressure_drop"] = pressure_drop

        state["tank_pressure"] -= pressure_drop

        # ----------------------------------------------------
        # Braking energy recovery
        # ----------------------------------------------------

        kinetic_energy_kj = (
            0.5
            * state["mass"]
            * speed_ms ** 2
            / 1000.0
        )

        braking_recovery = (
            kinetic_energy_kj
            * brake
            * ai["recovery"]
            * 0.04
        )

        braking_recovery = max(
            braking_recovery,
            0.0
        )

        state["braking_recovery_kj"] += (
            braking_recovery * dt
        )

        # ----------------------------------------------------
        # Flywheel
        # ----------------------------------------------------

        if brake > 0.05:

            rpm_gain = (
                braking_recovery
                * 120.0
                * dt
            )

            state["flywheel_rpm"] += rpm_gain

        elif ai["flywheel_assist"] and throttle > 0.3:

            rpm_loss = (
                throttle
                * 35.0
                * dt
            )

            state["flywheel_rpm"] -= rpm_loss

        else:

            state["flywheel_rpm"] -= 4.0 * dt

        state["flywheel_rpm"] = clamp(
            state["flywheel_rpm"],
            FLYWHEEL_MIN_RPM,
            FLYWHEEL_MAX_RPM
        )

        # ----------------------------------------------------
        # APERS / PRC
        # ----------------------------------------------------

        exhaust_energy = (
            state["air_flow"]
            * 18.0
            * dt
        )

        exhaust_recovery = (
            exhaust_energy
            * ai["recovery"]
            * 0.22
        )

        state["exhaust_recovery_kj"] += (
            exhaust_recovery
        )

        # ----------------------------------------------------
        # Flywheel total stored energy
        # ----------------------------------------------------

        state["flywheel_energy_kj"] = (
            flywheel_energy_kj(
                state["flywheel_rpm"]
            )
        )

        # ----------------------------------------------------
        # Energy accounting
        # ----------------------------------------------------

        input_energy = (
            state["air_flow"]
            * 900.0
            * dt
        )

        useful_energy = max(
            engine_power_kw * dt,
            0.0
        )

        state["total_energy_used_kj"] += (
            input_energy
        )

        state["useful_energy_kj"] += (
            useful_energy
        )

        recovered = (
            braking_recovery * dt
            + exhaust_recovery
        )

        state["total_energy_recovered_kj"] += (
            max(recovered, 0.0)
        )

        baseline_loss = (
            max(input_energy - useful_energy, 0.0)
        )

        state["baseline_energy_loss_kj"] += (
            baseline_loss
        )

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        state["distance_km"] += (
            state["speed"]
            * dt
            / 3600.0
        )

        # ----------------------------------------------------
        # Remaining range
        # ----------------------------------------------------

        remaining_energy = (
            air_energy_from_pressure(
                state["tank_pressure"]
            )
            * 1000.0
        )

        current_consumption = max(
            state["air_flow"] * 360.0,
            0.01
        )

        state["range_km"] = clamp(
            remaining_energy
            / current_consumption,
            0.0,
            500.0
        )

        # ----------------------------------------------------
        # Efficiency
        # ----------------------------------------------------

        used = max(
            state["total_energy_used_kj"],
            0.001
        )

        state["efficiency"] = clamp(
            (
                state["useful_energy_kj"]
                + state["total_energy_recovered_kj"]
            )
            / used
            * 100.0,
            0.0,
            100.0
        )

        # ----------------------------------------------------
        # Recovery percentage
        # ----------------------------------------------------

        state["recovery_percent"] = clamp(
            state["total_energy_recovered_kj"]
            / used
            * 100.0,
            0.0,
            100.0
        )

        # ----------------------------------------------------
        # Exhaust utilization
        # ----------------------------------------------------

        possible_exhaust = max(
            state["exhaust_recovery_kj"]
            / max(ai["recovery"], 0.1),
            0.001
        )

        state["exhaust_utilized_percent"] = clamp(
            state["exhaust_recovery_kj"]
            / possible_exhaust
            * 100.0,
            0.0,
            100.0
        )

        # ----------------------------------------------------
        # Energy Waste Analyzer
        # ----------------------------------------------------

        baseline = max(
            state["baseline_energy_loss_kj"],
            0.001
        )

        recovered_total = (
            state["total_energy_recovered_kj"]
        )

        state["energy_saved_percent"] = clamp(
            recovered_total
            / (baseline + recovered_total)
            * 100.0,
            0.0,
            100.0
        )

        # ----------------------------------------------------
        # Scenario
        # ----------------------------------------------------

        if brake > 0.2:
            state["scenario"] = "BRAKING"

        elif throttle > 0.7:
            state["scenario"] = "ACCELERATION"

        elif state["slope"] > 3:
            state["scenario"] = "UPHILL"

        elif state["slope"] < -3:
            state["scenario"] = "DOWNHILL"

        else:
            state["scenario"] = "CRUISE"

        state["engine_power_kw"] = engine_power_kw

        state["energy_available_kj"] = (
            air_energy_from_pressure(
                state["tank_pressure"]
            ) * 1000.0
        )

        state["wasted_energy_kj"] = max(
            state["total_energy_used_kj"]
            - state["useful_energy_kj"]
            - state["total_energy_recovered_kj"],
            0.0
        )

        state["last_update"] = time.time()


# ============================================================
# BACKGROUND SIMULATION
# ============================================================

def simulation_loop():

    while True:

        try:
            simulation_step(0.2)

        except Exception as error:
            print("Simulation error:", error)

        time.sleep(0.2)


# ============================================================
# API SERVER
# ============================================================

class AMEVHandler(BaseHTTPRequestHandler):

    def send_json(self, data):

        payload = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(payload))
        )

        self.send_header(
            "Cache-Control",
            "no-cache"
        )

        self.end_headers()

        self.wfile.write(payload)

    def send_html(self, html):

        payload = html.encode("utf-8")

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(payload))
        )

        self.end_headers()

        self.wfile.write(payload)

    def do_GET(self):

        parsed = urlparse(self.path)

        if parsed.path == "/":

            self.send_html(DASHBOARD)

        elif parsed.path == "/api/state":

            with state_lock:
                self.send_json(dict(state))

        elif parsed.path == "/api/reset":

            reset_state()

            with state_lock:
                self.send_json(dict(state))

        else:

            self.send_response(404)
            self.end_headers()

    def do_POST(self):

        parsed = urlparse(self.path)

        if parsed.path == "/api/control":

            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(length)

            try:
                data = json.loads(
                    body.decode("utf-8")
                )

                apply_controls(data)

                with state_lock:
                    self.send_json(dict(state))

            except Exception as error:

                self.send_json({
                    "error": str(error)
                })

        else:

            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


# ============================================================
# CONTROLS
# ============================================================

def apply_controls(data):

    with state_lock:

        if "throttle" in data:
            state["throttle"] = clamp(
                float(data["throttle"]),
                0.0,
                1.0
            )

        if "brake" in data:
            state["brake"] = clamp(
                float(data["brake"]),
                0.0,
                1.0
            )

        if "steering" in data:
            state["steering"] = clamp(
                float(data["steering"]),
                -1.0,
                1.0
            )

        if "slope" in data:
            state["slope"] = clamp(
                float(data["slope"]),
                -15.0,
                15.0
            )

        if "mass" in data:
            state["mass"] = clamp(
                float(data["mass"]),
                500.0,
                2000.0
            )

        if "temperature" in data:
            state["temperature"] = clamp(
                float(data["temperature"]),
                -10.0,
                60.0
            )

        if "tank_pressure" in data:
            state["tank_pressure"] = clamp(
                float(data["tank_pressure"]),
                20.0,
                300.0
            )


def reset_state():

    with state_lock:

        state["tank_pressure"] = 285.0
        state["speed"] = 42.0
        state["mass"] = 850.0
        state["slope"] = 0.0
        state["temperature"] = 25.0
        state["flywheel_rpm"] = 1850.0

        state["throttle"] = 0.0
        state["brake"] = 0.0
        state["steering"] = 0.0

        state["air_flow"] = 0.0
        state["pressure_drop"] = 0.0
        state["engine_power_kw"] = 0.0

        state["flywheel_energy_kj"] = 0.0
        state["braking_recovery_kj"] = 0.0
        state["exhaust_recovery_kj"] = 0.0

        state["total_energy_used_kj"] = 0.0
        state["total_energy_recovered_kj"] = 0.0
        state["baseline_energy_loss_kj"] = 0.0

        state["distance_km"] = 0.0
        state["range_km"] = 0.0

        state["efficiency"] = 0.0
        state["recovery_percent"] = 0.0
        state["energy_saved_percent"] = 0.0
        state["exhaust_utilized_percent"] = 0.0

        state["ai_mode"] = "IDLE"
        state["ai_message"] = "System reset"

        state["energy_available_kj"] = 0.0
        state["useful_energy_kj"] = 0.0
        state["wasted_energy_kj"] = 0.0

        state["scenario"] = "CRUISE"


# ============================================================
# HTML / CSS / JAVASCRIPT DASHBOARD
# ============================================================

DASHBOARD = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>AMEV-SIM</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #071018;
    color: #eaf4ff;
}

.header {
    padding: 22px;
    background: #0b1722;
    border-bottom: 1px solid #203445;
}

.header h1 {
    margin: 0;
    font-size: 28px;
}

.header p {
    margin: 7px 0 0;
    color: #8fa9bc;
}

.container {
    max-width: 1400px;
    margin: auto;
    padding: 18px;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px;
}

.card {
    background: #0d1b27;
    border: 1px solid #20384a;
    border-radius: 15px;
    padding: 17px;
    box-shadow: 0 5px 20px rgba(0,0,0,.2);
}

.card h3 {
    margin-top: 0;
    color: #8db7d4;
}

.value {
    font-size: 27px;
    font-weight: bold;
}

.unit {
    color: #7893a5;
    font-size: 13px;
}

.section {
    margin-top: 18px;
}

.section-title {
    font-size: 21px;
    font-weight: bold;
    margin-bottom: 12px;
}

.controls {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
}

.control {
    background: #0d1b27;
    border: 1px solid #20384a;
    border-radius: 15px;
    padding: 16px;
}

label {
    display: block;
    margin-bottom: 8px;
    color: #b9cfdd;
}

input[type=range] {
    width: 100%;
}

button {
    border: none;
    border-radius: 10px;
    padding: 13px 18px;
    margin: 4px;
    background: #163247;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #234c67;
}

button.danger {
    background: #682b31;
}

button.good {
    background: #205a45;
}

.status {
    padding: 14px;
    border-radius: 12px;
    background: #102b3a;
    border: 1px solid #28506a;
}

.ai {
    font-size: 19px;
    font-weight: bold;
}

.bar {
    width: 100%;
    height: 16px;
    background: #182b38;
    border-radius: 20px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    width: 0%;
    transition: width .25s;
    background: #4cb9e7;
}

.vehicle-area {
    position: relative;
    height: 260px;
    overflow: hidden;
    background:
        linear-gradient(
            #09131c 0 65%,
            #10222c 65% 100%
        );
    border-radius: 15px;
    border: 1px solid #20384a;
}

.road {
    position: absolute;
    bottom: 55px;
    left: 0;
    right: 0;
    height: 65px;
    border-top: 3px solid #5b7380;
    background: #15252e;
}

.vehicle {
    position: absolute;
    left: 45%;
    bottom: 82px;
    width: 150px;
    height: 55px;
    border-radius: 20px 30px 10px 10px;
    background: #4b86a6;
    transition: transform .2s;
}

.vehicle:before {
    content: "";
    position: absolute;
    width: 62px;
    height: 25px;
    right: 18px;
    top: -18px;
    border-radius: 15px 15px 0 0;
    background: #6ea6c3;
}

.wheel {
    position: absolute;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #101820;
    bottom: -13px;
}

.wheel.left {
    left: 20px;
}

.wheel.right {
    right: 20px;
}

.energy-flow {
    font-family: monospace;
    font-size: 16px;
    line-height: 2;
    text-align: center;
}

.flow-active {
    color: #64d8ff;
    font-weight: bold;
}

table {
    width: 100%;
    border-collapse: collapse;
}

td, th {
    padding: 10px;
    border-bottom: 1px solid #20384a;
    text-align: left;
}

.green {
    color: #5ee7a1;
}

.yellow {
    color: #ffd66b;
}

.red {
    color: #ff7777;
}

.small {
    font-size: 12px;
    color: #718999;
}

</style>

</head>

<body>

<div class="header">

<h1>🚗 AMEV-SIM</h1>

<p>
Adaptive Mechanical Energy Vehicle —
Intelligent Simulation & Digital Twin
</p>

</div>

<div class="container">

<!-- ================================================= -->
<!-- LIVE METRICS -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
📊 Live Simulation
</div>

<div class="grid">

<div class="card">
<h3>Tank Pressure</h3>
<div class="value" id="pressure">285</div>
<div class="unit">bar</div>
<div class="bar">
<div class="bar-fill" id="pressureBar"></div>
</div>
</div>

<div class="card">
<h3>Vehicle Speed</h3>
<div class="value" id="speed">42</div>
<div class="unit">km/h</div>
</div>

<div class="card">
<h3>Air Flow</h3>
<div class="value" id="airflow">0</div>
<div class="unit">kg/s</div>
</div>

<div class="card">
<h3>Flywheel RPM</h3>
<div class="value" id="rpm">1850</div>
<div class="unit">RPM</div>
</div>

<div class="card">
<h3>Estimated Range</h3>
<div class="value" id="range">0</div>
<div class="unit">km</div>
</div>

<div class="card">
<h3>Efficiency</h3>
<div class="value" id="efficiency">0</div>
<div class="unit">%</div>
</div>

<div class="card">
<h3>Energy Recovery</h3>
<div class="value" id="recovery">0</div>
<div class="unit">%</div>
</div>

<div class="card">
<h3>Engine Output</h3>
<div class="value" id="power">0</div>
<div class="unit">kW</div>
</div>

</div>

</div>


<!-- ================================================= -->
<!-- AI -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
🧠 Adaptive AI Energy Management
</div>

<div class="status">

<div class="ai" id="aiMode">
AI INITIALIZING
</div>

<p id="aiMessage">
Starting adaptive controller...
</p>

<p>
Scenario:
<strong id="scenario">CRUISE</strong>
</p>

</div>

</div>


<!-- ================================================= -->
<!-- DIGITAL TWIN -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
🚗 Digital Twin
</div>

<div class="vehicle-area">

<div class="road"></div>

<div class="vehicle" id="vehicle">

<div class="wheel left"></div>
<div class="wheel right"></div>

</div>

</div>

</div>


<!-- ================================================= -->
<!-- ENERGY FLOW -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
⚡ Live Energy Flow
</div>

<div class="card">

<div class="energy-flow">

<div id="tankFlow">
🫧 Compressed Air Tank
</div>

↓

<div id="engineFlow">
⚙️ Pneumatic Engine
</div>

↓

<div>
🚗 Vehicle Motion
</div>

↓

<div id="exhaustFlow">
💨 Exhaust Air
</div>

↓

<div>
♻️ APERS / PRC
</div>

↓

<div>
🔋 Flywheel / Buffer / Secondary Work
</div>

</div>

</div>

</div>


<!-- ================================================= -->
<!-- CONTROLS -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
🎮 Driving Controls
</div>

<div class="controls">

<div class="control">

<label>
Throttle:
<span id="throttleValue">0</span>%
</label>

<input
type="range"
id="throttle"
min="0"
max="100"
value="0"
oninput="controlChange()">

</div>


<div class="control">

<label>
Brake:
<span id="brakeValue">0</span>%
</label>

<input
type="range"
id="brake"
min="0"
max="100"
value="0"
oninput="controlChange()">

</div>


<div class="control">

<label>
Steering:
<span id="steeringValue">0</span>°
</label>

<input
type="range"
id="steering"
min="-100"
max="100"
value="0"
oninput="controlChange()">

</div>


<div class="control">

<label>
Road Slope:
<span id="slopeValue">0</span>%
</label>

<input
type="range"
id="slope"
min="-15"
max="15"
value="0"
step="0.5"
oninput="controlChange()">

</div>


<div class="control">

<label>
Vehicle Load:
<span id="massValue">850</span> kg
</label>

<input
type="range"
id="mass"
min="500"
max="2000"
value="850"
step="10"
oninput="controlChange()">

</div>


<div class="control">

<label>
Temperature:
<span id="temperatureValue">25</span>°C
</label>

<input
type="range"
id="temperature"
min="-10"
max="60"
value="25"
oninput="controlChange()">

</div>


<div class="control">

<label>
Tank Pressure:
<span id="tankValue">285</span> bar
</label>

<input
type="range"
id="tank"
min="20"
max="300"
value="285"
oninput="controlChange()">

</div>

</div>

<br>

<button class="good"
onclick="setDriving('accelerate')">
🚀 ACCELERATE
</button>

<button
onclick="setDriving('brake')">
🛑 BRAKE
</button>

<button
onclick="setDriving('cruise')">
🟢 CRUISE
</button>

<button class="danger"
onclick="resetSimulation()">
🔄 RESET
</button>

</div>


<!-- ================================================= -->
<!-- ENERGY WASTE ANALYZER -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
🔥 Energy Waste Analyzer
</div>

<div class="grid">

<div class="card">

<h3>Energy Saved</h3>

<div class="value green"
id="saved">
0
</div>

<div class="unit">
Simulation estimate %
</div>

</div>


<div class="card">

<h3>Braking Recovery</h3>

<div class="value"
id="brakeRecovery">
0
</div>

<div class="unit">
kJ recovered
</div>

</div>


<div class="card">

<h3>Exhaust Utilized</h3>

<div class="value"
id="exhaustRecovery">
0
</div>

<div class="unit">
kJ recovered
</div>

</div>


<div class="card">

<h3>Wasted Energy</h3>

<div class="value red"
id="wasted">
0
</div>

<div class="unit">
kJ
</div>

</div>

</div>

<br>

<table>

<tr>
<th>Energy Path</th>
<th>Status</th>
</tr>

<tr>
<td>Compressed Air → Engine</td>
<td id="path1">ACTIVE</td>
</tr>

<tr>
<td>Braking → Flywheel</td>
<td id="path2">READY</td>
</tr>

<tr>
<td>Exhaust → APERS / PRC</td>
<td id="path3">READY</td>
</tr>

<tr>
<td>APERS → Secondary Work</td>
<td id="path4">READY</td>
</tr>

</table>

<p class="small">
⚠️ All percentages and energy values shown here are
simulation/model outputs, not measured real-world performance.
</p>

</div>


<!-- ================================================= -->
<!-- SIMULATION DATA -->
<!-- ================================================= -->

<div class="section">

<div class="section-title">
📈 Simulation Data
</div>

<div class="card">

<table>

<tr>
<td>Available Energy</td>
<td id="availableEnergy">0 kJ</td>
</tr>

<tr>
<td>Useful Energy</td>
<td id="usefulEnergy">0 kJ</td>
</tr>

<tr>
<td>Total Energy Used</td>
<td id="totalUsed">0 kJ</td>
</tr>

<tr>
<td>Pressure Drop</td>
<td id="pressureDrop">0 bar/sim</td>
</tr>

<tr>
<td>Distance Travelled</td>
<td id="distance">0 km</td>
</tr>

<tr>
<td>Flywheel Stored Energy</td>
<td id="flywheelEnergy">0 kJ</td>
</tr>

</table>

</div>

</div>


<!-- ================================================= -->
<!-- FOOTER -->
<!-- ================================================= -->

<div class="section">

<div class="card">

<h3>AMEV-SIM Architecture</h3>

<p>
USER / SIMULATOR
↓
Driving Scenario
↓
Vehicle Simulator
↓
Adaptive Energy Engine
↓
AI Energy Management
↓
APERS / PRC Simulation
↓
Flywheel Recovery Model
↓
Energy Waste Analyzer
↓
Live Digital Twin Dashboard
</p>

</div>

</div>

</div>


<script>

let lastState = null;


function sendControls(data) {

    fetch("/api/control", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(data)

    });

}


function controlChange() {

    let throttle =
        Number(
            document.getElementById("throttle").value
        ) / 100;

    let brake =
        Number(
            document.getElementById("brake").value
        ) / 100;

    let steering =
        Number(
            document.getElementById("steering").value
        ) / 100;

    let slope =
        Number(
            document.getElementById("slope").value
        );

    let mass =
        Number(
            document.getElementById("mass").value
        );

    let temperature =
        Number(
            document.getElementById("temperature").value
        );

    let tank =
        Number(
            document.getElementById("tank").value
        );


    document.getElementById(
        "throttleValue"
    ).innerText =
        Math.round(throttle * 100);

    document.getElementById(
        "brakeValue"
    ).innerText =
        Math.round(brake * 100);

    document.getElementById(
        "steeringValue"
    ).innerText =
        Math.round(steering * 100);

    document.getElementById(
        "slopeValue"
    ).innerText =
        slope;

    document.getElementById(
        "massValue"
    ).innerText =
        mass;

    document.getElementById(
        "temperatureValue"
    ).innerText =
        temperature;

    document.getElementById(
        "tankValue"
    ).innerText =
        tank;


    sendControls({

        throttle: throttle,

        brake: brake,

        steering: steering,

        slope: slope,

        mass: mass,

        temperature: temperature,

        tank_pressure: tank

    });

}


function setDriving(mode) {

    if (mode === "accelerate") {

        document.getElementById(
            "throttle"
        ).value = 75;

        document.getElementById(
            "brake"
        ).value = 0;

    }

    if (mode === "brake") {

        document.getElementById(
            "throttle"
        ).value = 0;

        document.getElementById(
            "brake"
        ).value = 80;

    }

    if (mode === "cruise") {

        document.getElementById(
            "throttle"
        ).value = 25;

        document.getElementById(
            "brake"
        ).value = 0;

    }

    controlChange();

}


function resetSimulation() {

    fetch("/api/reset")
    .then(() => {

        document.getElementById(
            "throttle"
        ).value = 0;

        document.getElementById(
            "brake"
        ).value = 0;

        document.getElementById(
            "steering"
        ).value = 0;

        document.getElementById(
            "slope"
        ).value = 0;

        document.getElementById(
            "mass"
        ).value = 850;

        document.getElementById(
            "temperature"
        ).value = 25;

        document.getElementById(
            "tank"
        ).value = 285;

        controlChange();

    });

}


function setText(id, value, decimals=1) {

    document.getElementById(id).innerText =
        Number(value).toFixed(decimals);

}


function updateDashboard(s) {

    lastState = s;


    setText(
        "pressure",
        s.tank_pressure,
        1
    );

    setText(
        "speed",
        s.speed,
        1
    );

    setText(
        "airflow",
        s.air_flow,
        3
    );

    setText(
        "rpm",
        s.flywheel_rpm,
        0
    );

    setText(
        "range",
        s.range_km,
        1
    );

    setText(
        "efficiency",
        s.efficiency,
        1
    );

    setText(
        "recovery",
        s.recovery_percent,
        1
    );

    setText(
        "power",
        s.engine_power_kw,
        1
    );


    setText(
        "saved",
        s.energy_saved_percent,
        1
    );

    setText(
        "brakeRecovery",
        s.braking_recovery_kj,
        2
    );

    setText(
        "exhaustRecovery",
        s.exhaust_recovery_kj,
        2
    );

    setText(
        "wasted",
        s.wasted_energy_kj,
        2
    );


    setText(
        "availableEnergy",
        s.energy_available_kj,
        1
    );

    setText(
        "usefulEnergy",
        s.useful_energy_kj,
        1
    );

    setText(
        "totalUsed",
        s.total_energy_used_kj,
        1
    );

    setText(
        "pressureDrop",
        s.pressure_drop,
        2
    );

    setText(
        "distance",
        s.distance_km,
        3
    );

    setText(
        "flywheelEnergy",
        s.flywheel_energy_kj,
        2
    );


    document.getElementById(
        "aiMode"
    ).innerText =
        "🤖 " + s.ai_mode;

    document.getElementById(
        "aiMessage"
    ).innerText =
        s.ai_message;

    document.getElementById(
        "scenario"
    ).innerText =
        s.scenario;


    // Pressure bar

    document.getElementById(
        "pressureBar"
    ).style.width =
        Math.max(
            0,
            Math.min(
                100,
                s.tank_pressure / 3
            )
        ) + "%";


    // Vehicle tilt according to road slope

    document.getElementById(
        "vehicle"
    ).style.transform =
        "rotate(" +
        (-s.slope * 1.2) +
        "deg)";


    // Energy-flow highlighting

    let engine =
        document.getElementById(
            "engineFlow"
        );

    let exhaust =
        document.getElementById(
            "exhaustFlow"
        );

    let tank =
        document.getElementById(
            "tankFlow"
        );


    engine.classList.remove(
        "flow-active"
    );

    exhaust.classList.remove(
        "flow-active"
    );

    tank.classList.remove(
        "flow-active"
    );


    if (s.throttle > 0.05) {

        engine.classList.add(
            "flow-active"
        );

        tank.classList.add(
            "flow-active"
        );

    }

    if (s.brake > 0.05) {

        exhaust.classList.add(
            "flow-active"
        );

    }


    // Recovery status

    document.getElementById(
        "path2"
    ).innerText =
        s.brake > 0.05
        ? "RECOVERING"
        : "READY";


    document.getElementById(
        "path3"
    ).innerText =
        s.air_flow > 0.03
        ? "APERS ACTIVE"
        : "READY";


    document.getElementById(
        "path4"
    ).innerText =
        s.exhaust_recovery_kj > 0
        ? "SECONDARY WORK"
        : "READY";

}


async function fetchState() {

    try {

        const response =
            await fetch(
                "/api/state"
            );

        const data =
            await response.json();

        updateDashboard(data);

    }

    catch(error) {

        console.log(
            "Connection error:",
            error
        );

    }

}


setInterval(
    fetchState,
    300
);


fetchState();

</script>

</body>

</html>
"""


# ============================================================
# START SERVER
# ============================================================

def main():

    print()
    print("=" * 60)
    print("             AMEV-SIM STARTED")
    print("=" * 60)
    print()
    print("Digital Twin + Energy Simulation + AI Controller")
    print()
    print(f"Open your browser:")
    print(f"http://localhost:{PORT}")
    print()
    print("Press CTRL+C to stop.")
    print("=" * 60)
    print()

    # Start simulation engine
    thread = threading.Thread(
        target=simulation_loop,
        daemon=True
    )

    thread.start()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        AMEVHandler
    )

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print("\nAMEV-SIM stopped.")

    finally:

        server.server_close()


if __name__ == "__main__":
    main()