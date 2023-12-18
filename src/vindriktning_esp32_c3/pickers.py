import logging

from faebryk.core.core import Module
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.library.LED import LED
from faebryk.library.MOSFET import MOSFET
from faebryk.library.Range import Range
from faebryk.library.Resistor import Resistor
from faebryk.library.Switch import _TSwitch
from faebryk.library.USB_Type_C_Receptacle_24_pin import USB_Type_C_Receptacle_24_pin
from faebryk.libs.picker.lcsc import LCSC, attach_footprint
from faebryk.libs.picker.lcsc import LCSC_Part as LCSC_Part_Base
from faebryk.libs.picker.picker import (
    Part,
    PickerOption,
    pick_module_by_params,
)
from faebryk.libs.units import M, k, n, u
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.Mounting_Hole import Mounting_Hole
from vindriktning_esp32_c3.library.pf_74AHCT2G125 import pf_74AHCT2G125
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002
from vindriktning_esp32_c3.library.QWIIC import QWIIC
from vindriktning_esp32_c3.library.SCD40 import SCD40
from vindriktning_esp32_c3.library.TXS0102DCUR import TXS0102DCUR
from vindriktning_esp32_c3.library.USBLC6_2P6 import USBLC6_2P6
from vindriktning_esp32_c3.library.XL_3528RGBW_WS2812B import XL_3528RGBW_WS2812B

logger = logging.getLogger(__name__)


class LCSC_KicadOverride(LCSC):
    def attach(self, module: Module, part: Part):
        assert isinstance(part, LCSC_Part)
        attach_footprint(component=module, partno=part.partno)


class LCSC_Part(LCSC_Part_Base):
    def __init__(self, partno: str) -> None:
        Part.__init__(self, partno=partno, supplier=LCSC_KicadOverride())


def pick_capacitor(module: Capacitor):
    """
    Link a partnumber/footprint to a Capacitor

    Select capacitors
    """

    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C1525"),
                params={
                    "temperature_coefficient": Range(
                        Capacitor.TemperatureCoefficient.Y5V,
                        Capacitor.TemperatureCoefficient.X7R,
                    ),
                    "capacitance": Constant(100 * n),
                    "rated_voltage": Range(0, 16),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C380332"),
                params={
                    "temperature_coefficient": Range(
                        Capacitor.TemperatureCoefficient.Y5V,
                        Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": Constant(10 * u),
                    "rated_voltage": Range(0, 16),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C52923"),
                params={
                    "temperature_coefficient": Range(
                        Capacitor.TemperatureCoefficient.Y5V,
                        Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": Constant(1 * u),
                    "rated_voltage": Range(0, 25),
                },
            ),
            PickerOption(
                part=LCSC_Part(partno="C368809"),
                params={
                    "temperature_coefficient": Range(
                        Capacitor.TemperatureCoefficient.Y5V,
                        Capacitor.TemperatureCoefficient.X5R,
                    ),
                    "capacitance": Constant(4700 * n),
                    "rated_voltage": Range(0, 10),
                },
            ),
        ],
    )


def pick_resistor(resistor: Resistor):
    """
    Link a partnumber/footprint to a Resistor

    Selects resistors
    """

    pick_module_by_params(
        resistor,
        [
            PickerOption(
                part=LCSC_Part(partno="C137885"),
                params={"resistance": Constant(300)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C137997"),
                params={"resistance": Constant(390)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C226726"),
                params={"resistance": Constant(5.1 * k)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25741"),
                params={"resistance": Constant(100 * k)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C11702"),
                params={"resistance": Constant(1 * k)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25744"),
                params={"resistance": Constant(10 * k)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C305257"),
                params={"resistance": Constant(1 * M)},
            ),
        ],
    )


def pick_mosfet(module: MOSFET):
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
                    "channel_type": Constant(MOSFET.ChannelType.N_CHANNEL),
                },
                pinmap=standard_pinmap,
            ),
            PickerOption(
                part=LCSC_Part(partno="C8492"),
                params={
                    "channel_type": Constant(MOSFET.ChannelType.P_CHANNEL),
                },
                pinmap=standard_pinmap,
            ),
        ],
    )


def pick_part_recursively(module: Module):
    assert isinstance(module, Module)

    if isinstance(module, Resistor):
        pick_resistor(module)
    elif isinstance(module, Capacitor):
        pick_capacitor(module)
    elif isinstance(module, MOSFET):
        pick_mosfet(module)
    elif isinstance(module, ME6211C33M5G_N):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C82942"))])
    # elif isinstance(module, USB_Type_C_Receptacle_14_pin_Vertical):
    # pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C168704"))])
    elif isinstance(module, USB_Type_C_Receptacle_24_pin):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C134092"))])
    elif isinstance(module, LED):
        pick_module_by_params(
            module,
            [
                PickerOption(
                    part=LCSC_Part(partno="C84256"),
                    pinmap={
                        "1": module.IFs.anode,
                        "2": module.IFs.cathode,
                    },
                )
            ],
        )
    elif isinstance(module, ESP32_C3_MINI_1_VIND):
        # U ufl version
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C3013922"))])
        # Standard PCB antenna version
        # pick_module_by_params(#module, [PickerOption(part=LCSC_Part(partno="C2934569"))])
    elif isinstance(module, XL_3528RGBW_WS2812B):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C2890364"))])
    elif isinstance(module, HLK_LD2410B_P):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C5183132"))])
    elif isinstance(module, USBLC6_2P6):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C2827693"))])
    elif isinstance(module, TXS0102DCUR):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C53434"))])
    elif isinstance(module, BH1750FVI_TR):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C78960"))])
    elif isinstance(module, pf_74AHCT2G125):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C12494"))])
    elif isinstance(module, pf_533984002):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C393945"))])
    elif isinstance(module, B4B_ZR_SM4_TF):
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C145997"))])
    elif isinstance(module, QWIIC):
        # vertical version
        # pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C160404"))])
        # 90 degrees version
        pick_module_by_params(module, [PickerOption(part=LCSC_Part(partno="C495539"))])
    elif isinstance(module, SCD40):
        pick_module_by_params(
            module,
            [
                PickerOption(
                    part=LCSC_Part(partno="C3659421"),
                    pinmap={
                        "6": module.IFs.power.NODEs.lv,
                        "20": module.IFs.power.NODEs.lv,
                        "21": module.IFs.power.NODEs.lv,
                        "7": module.IFs.power.NODEs.hv,
                        "19": module.IFs.power.NODEs.hv,
                        "9": module.IFs.i2c.NODEs.scl.NODEs.signal,
                        "10": module.IFs.i2c.NODEs.sda.NODEs.signal,
                    },
                )
            ],
        )
    elif isinstance(module, _TSwitch):
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
    else:
        for child in module.NODEs.get_all():
            if not isinstance(child, Module):
                continue
            if child is module:
                continue
            # pick_part_recursively(child)
