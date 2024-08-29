import logging

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.picker.lcsc import LCSC_Part
from faebryk.libs.picker.picker import (
    PickerOption,
    pick_module_by_params,
)
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


def pick_mosfet(module: F.MOSFET):
    standard_pinmap = {
        "1": module.gate,
        "2": module.source,
        "3": module.drain,
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
                params={"resistance": F.Constant(100 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C474070"),
                params={"resistance": F.Constant(120 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C328302"),
                params={"resistance": F.Constant(150 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25087"),
                params={"resistance": F.Constant(200 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C137885"),
                params={"resistance": F.Constant(300 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C137997"),
                params={"resistance": F.Constant(390 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C284656"),
                params={"resistance": F.Constant(680 * P.ohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C11702"),
                params={"resistance": F.Constant(1 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25879"),
                params={"resistance": F.Constant(2.2 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25900"),
                params={"resistance": F.Constant(4.7 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25905"),
                params={"resistance": F.Constant(5.1 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25917"),
                params={"resistance": F.Constant(6.8 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25744"),
                params={"resistance": F.Constant(10 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25752"),
                params={"resistance": F.Constant(12 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25771"),
                params={"resistance": F.Constant(27 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25741"),
                params={"resistance": F.Constant(100 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25782"),
                params={"resistance": F.Constant(390 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25790"),
                params={"resistance": F.Constant(470 * P.kohm)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C305257"),
                params={"resistance": F.Constant(1 * P.Mohm)},
            ),
        ],
    )


def pick_capacitor(module: F.Capacitor):
    """
    Link a partnumber/footprint to a Capacitor

    Uses 0402 when possible
    """

    c = module.capacitance.get_most_narrow()

    if isinstance(c, F.Range):
        c = F.Range(c.min.get_most_narrow(), c.max.get_most_narrow())
        if(isinstance(c, F.Range) or isinstance(c, F.Range)):
            logger.warning(f"Capacitance has double range: {module.capacitance}")
            module.capacitance.min.override(module.capacitance.min.max)
            logger.warning(f"New capacitance: {module.capacitance}")
            exit(1)

    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C52923"),
                params={
                    "temperature_coefficient": F.Constant(
                        F.Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": F.Constant(1 * P.uF),
                    "rated_voltage": F.Constant(25 * P.V),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C1525"),
                params={
                    "temperature_coefficient": F.Constant(
                        F.Capacitor.TemperatureCoefficient.X7R,
                    ),
                    "capacitance": F.Constant(100 * P.nF),
                    "rated_voltage": F.Constant(16 * P.V),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C86057"),
                params={
                    "temperature_coefficient": F.Constant(
                        F.Capacitor.TemperatureCoefficient.X7R,
                    ),
                    "capacitance": F.Constant(100 * P.nF),
                    "rated_voltage": F.Constant(1000 * P.V),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C368809"),
                params={
                    "temperature_coefficient": F.Constant(
                        F.Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": F.Constant(4700 * P.nF),
                    "rated_voltage": F.Constant(10 * P.V),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C19702"),
                params={
                    "temperature_coefficient": F.Constant(
                        F.Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": F.Constant(10 * P.uF),
                    "rated_voltage": F.Constant(10 * P.V),
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
                    "max_brightness": F.Constant(285 * P.mcandela),
                    "forward_voltage": F.Constant(3.7 * P.V),
                    "max_current": F.Constant(100 * P.mA),
                },
                pinmap={"1": module.cathode, "2": module.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C72041"),
                params={
                    "color": F.Constant(F.LED.Color.BLUE),
                    "max_brightness": F.Constant(28.5 * P.mcandela),
                    "forward_voltage": F.Constant(3.1 * P.V),
                    "max_current": F.Constant(100 * P.mA),
                },
                pinmap={"1": module.cathode, "2": module.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C72038"),
                params={
                    "color": F.Constant(F.LED.Color.YELLOW),
                    "max_brightness": F.Constant(180 * P.mcandela),
                    "forward_voltage": F.Constant(2.3 * P.V),
                    "max_current": F.Constant(60 * P.mA),
                },
                pinmap={"1": module.cathode, "2": module.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C84256"),
                params={
                    "color": F.Constant(F.LED.Color.RED),
                    "max_brightness": F.Constant(195 * P.mcandela),
                    "forward_voltage": F.Constant(2.0 * P.V),
                    "max_current": F.Constant(25 * P.mA),
                },
                pinmap={
                    "1": module.anode,
                    "2": module.cathode,
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
                    "trip_current": F.Constant(1 * P.A),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C914085"),
                params={
                    "fuse_type": F.Constant(F.Fuse.FuseType.RESETTABLE),
                    "response_type": F.Constant(F.Fuse.ResponseType.SLOW),
                    "trip_current": F.Constant(0.5 * P.A),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C70050"),
                params={
                    "fuse_type": F.Constant(F.Fuse.FuseType.RESETTABLE),
                    "response_type": F.Constant(F.Fuse.ResponseType.SLOW),
                    "trip_current": F.Constant(0.550 * P.A),
                },
            ),
        ],
    )


def add_app_pickers(module: Module):
    # switch over all types of parts you want to assign real components to
    assert isinstance(module, Module)
    lookup = {
        F.Resistor: pick_resistor,
        F.Capacitor: pick_capacitor,
        F.LED: pick_led,
        F.Fuse: pick_fuse,
        F.MOSFET: pick_mosfet,
        F.USB_Type_C_Receptacle_14_pin_Vertical: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C168704"))]
        ),
        F.USB_Type_C_Receptacle_24_pin: (
            lambda x: pick_module_by_params(
                x, [PickerOption(part=LCSC_Part(partno="C134092"))]
            )
        ),
        F.LED: pick_led,
        F.ESP32_C3_MINI_1: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C3013922"))]
        ),
        F.TXS0102DCUR: lambda x: pick_module_by_params(
            x,
            [
                PickerOption(
                    part=LCSC_Part(partno="C53434"),
                    pinmap={
                        "1": x.shifters[1].io_b.signal,
                        "2": x.voltage_a_power.lv,
                        "3": x.voltage_a_power.hv,
                        "4": x.shifters[1].io_a.signal,
                        "5": x.shifters[0].io_a.signal,
                        "6": x.n_oe.signal,
                        "7": x.voltage_b_power.hv,
                        "8": x.shifters[0].io_b.signal,
                    },
                )
            ],
        ),
        F.QWIIC: lambda x: pick_module_by_params(
            x,
            [
                PickerOption(
                    part=LCSC_Part(partno="C495539"),
                    pinmap={
                        "1": x.power.lv,
                        "2": x.power.hv,
                        "3": x.i2c.sda.signal,
                        "4": x.i2c.scl.signal,
                    },
                )
            ],
        ),
        # TODO: F.Switch(F.Electrical).is_instance(module):
        F.Button: lambda x: pick_module_by_params(
            x,
            [
                PickerOption(
                    part=LCSC_Part(partno="C139797"),
                    pinmap={
                        "1": x.unnamed[0],
                        "2": x.unnamed[0],
                        "3": x.unnamed[1],
                        "4": x.unnamed[1],
                    },
                )
            ],
        ),
        F.Fuse: pick_fuse,
        F.USB2_0_ESD_Protection: lambda x: pick_module_by_params(
            x,
            [
                # USBLC6_2P6
                PickerOption(
                    part=LCSC_Part(partno="C2827693"),
                    pinmap={
                        "1": x.usb[0].usb_if.d.p,
                        "2": x.usb[0].usb_if.buspower.lv,
                        "3": x.usb[0].usb_if.d.n,
                        "4": x.usb[1].usb_if.d.n,
                        "5": x.usb[0].usb_if.buspower.hv,
                        "6": x.usb[1].usb_if.d.p,
                    },
                )
            ],
        ),
        F.SCD40: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C3659421"))]
        ),
        F.ME6211C33M5G_N: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C82942"))]
        ),
        F.XL_3528RGBW_WS2812B: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C2890364"))]
        ),
        F.pf_533984002: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C393945"))]
        ),
        F.B4B_ZR_SM4_TF: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C145997"))]
        ),
        F.HLK_LD2410B_P: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C5183132"))]
        ),
        F.BH1750FVI_TR: lambda x: pick_module_by_params(
            x, [PickerOption(part=LCSC_Part(partno="C78960"))]
        ),
        F.Diode: lambda x: pick_module_by_params(
            x,
            [
                PickerOption(
                    part=LCSC_Part(partno="C64898"),
                    params={
                        "forward_voltage": F.Constant(1.1 * P.V),
                        "max_current": F.Constant(1 * P.A),
                    },
                    pinmap={
                        "2": x.anode,
                        "1": x.cathode,
                    },
                )
            ],
        ),
    }

    F.has_multi_picker.add_pickers_by_type(
        module,
        lookup,
        F.has_multi_picker.FunctionPicker,
    )
