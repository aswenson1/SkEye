---
icon: lucide/microchip
---

# Controller PCB

The SkEye controller is a physical I/O board built around a socketed Raspberry Pi
Pico or Pico H. It gives the host system simple controls and visible state without
placing camera or projector traffic on the microcontroller.

## Interfaces

| Interface | Design intent |
| --- | --- |
| Start button | Active-low input on `GP14` |
| Pause button | Active-low input on `GP15` |
| Reset button | Active-low input on `GP16` |
| Run LED | Status output on `GP17` |
| Track LED | Status output on `GP18` |
| Fault LED | Status output on `GP19` |
| Development UART | 3.3 V TX/RX on `GP0` and `GP1` |

The board also includes a power indicator, decoupling capacitors, four M3
mounting holes, and sockets for the Pico module. See the complete
[pin assignment table](pinout.md).

## Source files

| File | Purpose |
| --- | --- |
| `SkEye_Controller.kicad_sch` | Electrical schematic |
| `SkEye_Controller.kicad_pcb` | PCB layout |
| `SkEye_Controller.kicad_pro` | KiCad project settings |
| `SkEye.kicad_sym` | Project symbol library |
| `SkEye.pretty/` | Project footprint library |
| `models/` | Local STEP models |
| `documentation/BOM.csv` | Current bill of materials |

[Browse the controller source](https://github.com/aswenson1/SkEye/tree/main/hardware/SkEye_Controller)

## Validation checklist

- [ ] Run native KiCad electrical rules checking (ERC).
- [ ] Run native KiCad design rules checking (DRC).
- [ ] Review generated fabrication outputs.
- [ ] Assemble a prototype.
- [ ] Test every button, LED, UART signal, and power path.
- [ ] Record any accepted rule exclusions in the design files.

## Status

The design is preliminary.
