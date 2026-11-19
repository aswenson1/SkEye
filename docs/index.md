---
title: SkEye
description: Documentation for the SkEye tabletop mapping system.
hide:
  - toc
---

<div class="skeye-hero" markdown>
<div class="skeye-hero__copy" markdown>

<span class="skeye-kicker">SKEYE / DOCUMENTATION</span>

# SkEye

SkEye is a tabletop mapping system. It tracks physical objects and displays
information around them.

[System](system/overview.md){ .md-button .md-button--primary }
[Hardware](hardware/index.md){ .md-button }

</div>
<figure class="skeye-hero__media">
  <img src="assets/images/skeye-preview.webp" alt="Rendered preview of the SkEye tabletop camera and projector structure">
  <figcaption>Current mechanical concept render</figcaption>
</figure>
</div>

## System

<div class="skeye-card-grid" markdown>

<div class="skeye-card" markdown>

### Camera

Captures markers and objects on the table.

</div>

<div class="skeye-card" markdown>

### Host

Converts detections into positions and application state.

</div>

<div class="skeye-card" markdown>

### Output

Displays information in the physical workspace.

</div>

</div>

## Repository

The repository contains the mechanical model and a preliminary Raspberry Pi Pico
controller PCB. The `software/` directory is currently empty.

Controller status: ERC, DRC, and hardware testing have not been completed.

[Source](https://github.com/aswenson1/SkEye){ .md-button }
[Pitch](https://youtu.be/Z7oEOcuJgw8){ .md-button }

