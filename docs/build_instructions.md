# Build instructions

## Hardware

### PCBA

The first step is to order the printed circuit boards (PCB) with the components all assembled on there. If you want to assemble the components yourself, you don't need this guide :smile:.

Most of the time a PCB manufacturer expexts a .zip file from you containing so called *gerber* files. These files are describing your PCB design in a way that the software and the machines in the factory can use it.

The latest gerber file package can be found [here](https://github.com/ruben-iteng/vindrikning-esp32-c3/releases/latest) as `gerber.zip`.

All artifacts of this project are compatible with [JLCPCB](https://jlcpcb.com/) for pcb assembly. Most other manufacturers should work as well.

### Assembly

#### Disassemble the VINDRIKNING

- Loosen the 4 philips size #1 screws on the back of the VINDRIKNING.
- Remove the back cover.
- Slide out the PM sennsor.
- Carefully unplug the 2 PM sensor connectors on the PCB side.
- Remove the 4 philips size #1 screws holding the PCB in place.
- Place your new PCB in the VINDRIKNING front part of the case.
- Screw the 4 philips size #1 screws back in place.
- Plug in the 2 PM sensor connectors.
- Slide in the PM sensor in the back of the casing.
- Make shure everything is in place and screw the back cover back on.

#### Flashing the firmware

- Download the firmware from the [latest release](https://github.com/ruben-iteng/vindrikning-esp32-c3/releases/latest) as `firmware.bin`.
- Connect the VINDRIKNING to your computer using a USB-C cable.
- Press and hold the `BOOT` button on the VINDRIKNING (use a toothpick from the back of the VINDRIKNING).
- Press and hold the `RESET` button on the VINDRIKNING.
- Release the `RESET` button.
- Release the `BOOT` button.
- The VINDRIKNING is now in bootloader mode.
- Open a browser with support for WebUSB (e.g. Chrome).
- Go to [https://web.esphome.io/](https://web.esphome.io/).
- Click on `Connect` and select your device.
- Click `Install` and select the firmware file you downloaded earlier.
- Wait for the firmware to be uploaded.
- If you click on `Logs` you should see the VINDRIKNING booting up and spitting out some debug information.
- Now you can add it to your Home Assistant.
- Done!
