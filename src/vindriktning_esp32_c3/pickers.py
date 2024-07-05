import logging

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.picker.lcsc import LCSC_Part
from faebryk.libs.picker.picker import (
    PickerOption,
    pick_module_by_params,
)
from faebryk.libs.units import M, n, u
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND
from vindriktning_esp32_c3.library.QWIIC import QWIIC
from vindriktning_esp32_c3.library.TXS0102DCUR import TXS0102DCUR
from vindriktning_esp32_c3.library.USBLC6_2P6 import USBLC6_2P6

logger = logging.getLogger(__name__)


def pick_mosfet(module: F.MOSFET):
    standard_pinmap = {
        "1": module.IFs.gate,
        "2": module.IFs.source,
        "3": module.IFs.drain,
    }
    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C8545"),
                params={
                    "channel_type": F.Constant(F.MOSFET.ChannelType.N_CHANNEL),
                },
                pinmap=standard_pinmap,
            ),
            PickerOption(
                part=LCSC_Part(partno="C8492"),
                params={
                    "channel_type": F.Constant(F.MOSFET.ChannelType.P_CHANNEL),
                },
                pinmap=standard_pinmap,
            ),
        ],
    )


def pick_resistor(resistor: F.Resistor):
    """
    Link a partnumber/footprint to a Resistor

    Selects only 1% 0402 resistors
    """

    pick_module_by_params(
        resistor,
        [
            PickerOption(
                part=LCSC_Part(partno="C25076"),
                params={"resistance": F.Constant(100)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C474070"),
                params={"resistance": F.Constant(120)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C328302"),
                params={"resistance": F.Constant(150)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25087"),
                params={"resistance": F.Constant(200)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C137885"),
                params={"resistance": F.Constant(300)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C137997"),
                params={"resistance": F.Constant(390)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C284656"),
                params={"resistance": F.Constant(680)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C11702"),
                params={"resistance": F.Constant(1e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25879"),
                params={"resistance": F.Constant(2.2e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25900"),
                params={"resistance": F.Constant(4.7e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25905"),
                params={"resistance": F.Constant(5.1e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25917"),
                params={"resistance": F.Constant(6.8e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25744"),
                params={"resistance": F.Constant(10e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25752"),
                params={"resistance": F.Constant(12e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25771"),
                params={"resistance": F.Constant(27e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25741"),
                params={"resistance": F.Constant(100e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25782"),
                params={"resistance": F.Constant(390e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25790"),
                params={"resistance": F.Constant(470e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C305257"),
                params={"resistance": F.Constant(1 * M)},
            ),
        ],
    )


def pick_capacitor(module: F.Capacitor):
    """
    Link a partnumber/footprint to a Capacitor

    Uses 0402 when possible
    """

    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C52923"),
                params={
                    "temperature_coefficient": F.Range(
                        F.Capacitor.TemperatureCoefficient.Y5V,
                        F.Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": F.Constant(1 * u),
                    "rated_voltage": F.Range(0, 25),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C1525"),
                params={
                    "temperature_coefficient": F.Range(
                        F.Capacitor.TemperatureCoefficient.Y5V,
                        F.Capacitor.TemperatureCoefficient.X7R,
                    ),
                    "capacitance": F.Constant(100 * n),
                    "rated_voltage": F.Range(0, 16),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C368809"),
                params={
                    "temperature_coefficient": F.Range(
                        F.Capacitor.TemperatureCoefficient.Y5V,
                        F.Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": F.Constant(4700 * n),
                    "rated_voltage": F.Range(0, 10),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C19702"),
                params={
                    "temperature_coefficient": F.Range(
                        F.Capacitor.TemperatureCoefficient.Y5V,
                        F.Capacitor.TemperatureCoefficient.X7R,
                    ),
                    "capacitance": F.Constant(10e-6),
                    "rated_voltage": F.Range(0, 10),
                },
            ),
        ],
    )


def pick_led(module: F.LED):
    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C72043"),
                params={
                    "color": F.Constant(F.LED.Color.GREEN),
                    "max_brightness": F.Constant(285e-3),
                    "forward_voltage": F.Constant(3.7),
                    "max_current": F.Constant(100e-3),
                },
                pinmap={"1": module.IFs.cathode, "2": module.IFs.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C72041"),
                params={
                    "color": F.Constant(F.LED.Color.BLUE),
                    "max_brightness": F.Constant(28.5e-3),
                    "forward_voltage": F.Constant(3.1),
                    "max_current": F.Constant(100e-3),
                },
                pinmap={"1": module.IFs.cathode, "2": module.IFs.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C72038"),
                params={
                    "color": F.Constant(F.LED.Color.YELLOW),
                    "max_brightness": F.Constant(180e-3),
                    "forward_voltage": F.Constant(2.3),
                    "max_current": F.Constant(60e-3),
                },
                pinmap={"1": module.IFs.cathode, "2": module.IFs.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C84256"),
                params={
                    "color": F.Constant(F.LED.Color.RED),
                    "max_brightness": F.Constant(195e-3),
                    "forward_voltage": F.Constant(2.0),
                    "max_current": F.Constant(25e-3),
                },
                pinmap={
                    "1": module.IFs.anode,
                    "2": module.IFs.cathode,
                },
            ),
        ],
    )


def pick_fuse(module: F.Fuse):
    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C914087"),
                params={
                    "fuse_type": F.Constant(F.Fuse.FuseType.RESETTABLE),
                    "response_type": F.Constant(F.Fuse.ResponseType.SLOW),
                    "trip_current": F.Constant(1),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C914085"),
                params={
                    "fuse_type": F.Constant(F.Fuse.FuseType.RESETTABLE),
                    "response_type": F.Constant(F.Fuse.ResponseType.SLOW),
                    "trip_current": F.Constant(0.5),
                },
            ),
        ],
    )


def pick(module: Module):
    if isinstance(module, F.Resistor):
        pick_resistor(module)
    elif isinstance(module, F.Capacitor):
        pick_capacitor(module)
    elif isinstance(module, F.MOSFET):
        pick_mosfet(module)
    # elif isinstance(module, USB_Type_C_Receptacle_14_pin_Vertical):
    # pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C168704"))])
    elif isinstance(module, F.USB_Type_C_Receptacle_24_pin):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C134092"))])
    elif isinstance(module, F.LED):
        pick_led(module)
    elif isinstance(module, ESP32_C3_MINI_1_VIND):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C3013922"))])
    elif isinstance(module, TXS0102DCUR):
        pick_module_by_params(
            module,
            [
                PickerOption(
                    part=LCSC_Part(partno="C53434"),
                    pinmap={
                        "1": module.NODEs.shifters[1].IFs.io_b.IFs.signal,
                        "2": module.IFs.voltage_a_power.IFs.lv,
                        "3": module.IFs.voltage_a_power.IFs.hv,
                        "4": module.NODEs.shifters[1].IFs.io_a.IFs.signal,
                        "5": module.NODEs.shifters[0].IFs.io_a.IFs.signal,
                        "6": module.IFs.n_oe.IFs.signal,
                        "7": module.IFs.voltage_b_power.IFs.hv,
                        "8": module.NODEs.shifters[0].IFs.io_b.IFs.signal,
                    },
                )
            ],
        )
    elif isinstance(module, QWIIC):
        pick_module_by_params(
            module,
            [
                PickerOption(
                    part=LCSC_Part(partno="C495539"),
                    pinmap={
                        "1": module.IFs.power.IFs.lv,
                        "2": module.IFs.power.IFs.hv,
                        "3": module.IFs.i2c.IFs.sda.IFs.signal,
                        "4": module.IFs.i2c.IFs.scl.IFs.signal,
                    },
                )
            ],
        )
    elif isinstance(module, F.Switch(F.Electrical)):
        pick_module_by_params(
            module,
            [
                PickerOption(
                    part=LCSC_Part(partno="C139797"),
                    pinmap={
                        "1": module.IFs.unnamed[0],
                        "2": module.IFs.unnamed[0],
                        "3": module.IFs.unnamed[1],
                        "4": module.IFs.unnamed[1],
                    },
                )
            ],
        )
    elif isinstance(module, USBLC6_2P6):
        pick_module_by_params(
            module,
            [
                PickerOption(
                    part=LCSC_Part(partno="C2827693"),
                    pinmap={
                        "1": module.IFs.usb.IFs.d.IFs.p,
                        "2": module.IFs.usb.IFs.buspower.IFs.lv,
                        "3": module.IFs.usb.IFs.d.IFs.n,
                        "4": module.IFs.usb.IFs.d.IFs.n,
                        "5": module.IFs.usb.IFs.buspower.IFs.hv,
                        "6": module.IFs.usb.IFs.d.IFs.p,
                    },
                )
            ],
        )
    elif isinstance(module, F.Fuse):
        pick_fuse(module)
    else:
        return False

    return True
