---
icon: lucide/circuit-board
---

# Hardware

The current hardware work covers the overhead mechanical concept and a dedicated
physical I/O controller.

<div class="skeye-card-grid skeye-card-grid--two" markdown>

<div class="skeye-card" markdown>

## Enclosure and mount

The Blender model captures the current base, upright tube, equipment head, and
joint concepts.

[View enclosure renders](enclosure.md)

</div>

<div class="skeye-card" markdown>

## Controller PCB

The KiCad design hosts a Raspberry Pi Pico, three buttons, status LEDs, and a
3.3 V UART header.

[View controller details](controller.md)

</div>

</div>

## Source-of-truth files

The `.blend`, `.kicad_sch`, and `.kicad_pcb` files are the design sources. Images,
tables, fabrication files, and future interactive views are derived artifacts and
should be regenerated after relevant source changes.

## Status

The controller is preliminary. Native KiCad ERC/DRC and physical hardware testing
have not been completed.

