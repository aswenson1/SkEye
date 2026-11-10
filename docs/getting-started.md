---
icon: lucide/rocket
---

# Get started

Use this guide to explore the repository or work on its documentation. Runtime
setup instructions will be added when the host software lands in `software/`.

## Prerequisites

- [Git](https://git-scm.com/)
- Python 3.12 or newer for the documentation toolchain
- [KiCad](https://www.kicad.org/) for controller design files
- [Blender](https://www.blender.org/) for the mechanical concept model

## Clone the repository

```bash
git clone git@github.com:aswenson1/SkEye.git
cd SkEye
```

## Find the design files

| Area | Location | Primary tool |
| --- | --- | --- |
| Mechanical model | `hardware/models/skeye_compact.blend` | Blender |
| Mechanical renders | `hardware/models/renders/` | Any image viewer |
| Controller schematic | `hardware/SkEye_Controller/SkEye_Controller.kicad_sch` | KiCad |
| Controller PCB | `hardware/SkEye_Controller/SkEye_Controller.kicad_pcb` | KiCad |
| Controller BOM | `hardware/SkEye_Controller/documentation/BOM.csv` | Spreadsheet editor |
| Pin assignments | `hardware/SkEye_Controller/documentation/Pin_Assignments.csv` | Spreadsheet editor |

## Preview this site

=== "Linux and macOS"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements-docs.txt
    zensical serve
    ```

=== "Windows PowerShell"

    ```powershell
    py -m venv .venv
    .venv\Scripts\Activate.ps1
    py -m pip install -r requirements-docs.txt
    zensical serve
    ```

Open <http://127.0.0.1:8000>. Zensical watches the documentation files and
refreshes the preview as they change.

## Documentation map

- Read the [system overview](system/overview.md).
- See the [hardware files](hardware/index.md).
- See the [documentation workflow](contributing/documentation.md).

