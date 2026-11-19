---
icon: lucide/list-tree
---

# Controller pin assignments

The table below highlights assigned GPIO. All other Pico GPIO pins are currently
unconnected on the carrier.

| Pico physical pin | Pico signal | Carrier net | Function |
| ---: | --- | --- | --- |
| 1 | `GP0` | `UART_TX` | 3.3 V development UART transmit |
| 2 | `GP1` | `UART_RX` | 3.3 V development UART receive |
| 19 | `GP14` | `BTN_START_N` | Active-low start button |
| 20 | `GP15` | `BTN_PAUSE_N` | Active-low pause button |
| 21 | `GP16` | `BTN_RESET_N` | Active-low reset button |
| 22 | `GP17` | `LED_RUN` | Run status LED |
| 24 | `GP18` | `LED_TRACK` | Tracking status LED |
| 25 | `GP19` | `LED_FAULT` | Fault status LED |
| 36 | `3V3_OUT` | `+3V3` | Carrier 3.3 V rail |

Ground is connected on Pico physical pins 3, 8, 13, 18, 23, 28, and 38, with
analog ground on pin 33 also connected to the carrier ground net.

## Source data

The complete table is stored in
[`Pin_Assignments.csv`](https://github.com/aswenson1/SkEye/blob/main/hardware/SkEye_Controller/documentation/Pin_Assignments.csv).
Update that file and this page together until the table is generated during the
documentation build.

