 AMEV — Adaptive Mechanical Energy Vehicle

Exploring Alternative Propulsion and Intelligent Energy Management

AMEV is a vehicle research and simulation project exploring compressed-air propulsion, intelligent system monitoring, and experimental mechanical energy recovery.

The project aims to study alternative mobility concepts through software simulation, engineering design, and future prototype development.

---

Problem Statement

Conventional transportation systems face challenges related to energy consumption, environmental impact, and efficient energy utilisation. AMEV explores an alternative propulsion approach and investigates opportunities to monitor and study energy use in a vehicle system.

 Proposed Solution

AMEV explores a compressed-air-based propulsion concept combined with intelligent monitoring and experimental mechanical energy recovery.

The proposed system includes:

* Pneumatic propulsion: Investigating the conversion of stored compressed-air energy into mechanical motion.
* Intelligent monitoring: Exploring sensor-based monitoring and control using an ESP32.
* Flywheel energy recovery: Studying the potential to capture and reuse mechanical energy.
* Simulation platform: Developing a Python-based simulation to explore system behaviour and vehicle parameters.
* Future prototype development:Planning controlled experiments to evaluate the concept.

Technology Stack

* Python
* HTTP server modules from the Python standard library
* ESP32 — planned for hardware monitoring
* Mechanical and pneumatic system concepts

📁 Project Files

| File                       | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `AMEV_concpt document.pdf` | Project concept document                         |
| `AMEV_Presentation.pptx`   | Project presentation                             |
| `amev sim 1.py`            | Python simulation source code                    |
| `amev 3d sim.py`           | Additional simulation source code, if applicable |

▶️ Running the Python Simulation

1. Install Python 3 on your computer.
2. Download or clone this repository.
3. Open a terminal in the folder containing the Python file.
4. Run the simulation using the appropriate filename.

Example:

```bash
python "amev sim 1.py"
```

If the simulation starts a local HTTP server, open the address specified in the source code in your browser.

Note: The exact execution steps depend on the selected simulation file and its implementation.

Development Status

Current stage:Concept development and software simulation.

The project is being developed progressively. Hardware integration, prototype testing, and performance validation remain future development activities.

 Technical Considerations

Compressed-air systems require energy to compress and store air. Actual performance depends on storage pressure, tank capacity, pneumatic motor efficiency, leakage, expansion cooling, and mechanical losses.

Flywheel recovery and other proposed energy-recovery concepts require experimental validation. This project does not claim free energy or demonstrated net-energy generation.

Any physical prototype must use appropriately rated pressure vessels, regulators, pressure gauges, and pressure-relief devices.

 Future Development

* Validate and improve the Python simulation.
* Develop a physical prototype.
* Integrate sensors and an ESP32 controller.
* Measure pressure, temperature, speed, and energy consumption.
* Evaluate flywheel-based energy recovery experimentally.
* Compare measured results with simulation outputs.

 Contributions

Suggestions, technical discussions, and constructive feedback are welcome.

📌 Disclaimer

AMEV is an engineering research project exploring alternative propulsion and energy-management concepts. Proposed features and performance benefits must be verified through testing before being considered demonstrated results.
