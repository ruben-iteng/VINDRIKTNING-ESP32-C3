import faebryk.libs.picker.lcsc as lcsc
from faebryk.core.core import Module, Parameter
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Constant import Constant
from faebryk.library.has_resistance import has_resistance
from faebryk.library.LED import LED
from faebryk.library.TBD import TBD
from faebryk.library.MOSFET import MOSFET
from faebryk.library.Range import Range
from faebryk.library.Resistor import Resistor
from faebryk.library.Capacitor import Capacitor
from faebryk.library.USB_Type_C_Receptacle_24_pin import USB_Type_C_Receptacle_24_pin
from faebryk.libs.units import k, n, u
from faebryk.library.has_defined_type_description import has_defined_type_description

from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.SCD40 import SCD40
from vindriktning_esp32_c3.library.pf_74AHCT2G125 import pf_74AHCT2G125
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002
from vindriktning_esp32_c3.library.XL_3528RGBW_WS2812B import XL_3528RGBW_WS2812B

# from vindriktning_esp32_c3.library.USB_Type_C_Receptacle_14_pin_Vertical import (
#     USB_Type_C_Receptacle_14_pin_Vertical,
# )


def pick_component(cmp: Module):
    def _find_partno() -> str | None:
        if isinstance(cmp, ESP32_C3_MINI_1_VIND):
            return "C3013922"  # U ufl version
            # return "C2934569"  # Standard PCB antenna version

        if isinstance(cmp, HLK_LD2410B_P):
            return "C5183132"

        if isinstance(cmp, SCD40):
            cmp.add_trait(
                can_attach_to_footprint_via_pinmap(
                    {
                        "6": cmp.IFs.power.NODEs.lv,
                        "20": cmp.IFs.power.NODEs.lv,
                        "21": cmp.IFs.power.NODEs.lv,
                        "7": cmp.IFs.power.NODEs.hv,
                        "19": cmp.IFs.power.NODEs.hv,
                        "9": cmp.IFs.i2c.NODEs.scl.NODEs.signal,
                        "10": cmp.IFs.i2c.NODEs.sda.NODEs.signal,
                    }
                )
            )
            return "C3659421"

        # if isinstance(cmp, SK9822_EC20):
        #    return "C2909059"

        if isinstance(cmp, XL_3528RGBW_WS2812B):
            return "C2890364"

        if isinstance(cmp, BH1750FVI_TR):
            return "C78960"

        if isinstance(cmp, pf_74AHCT2G125):
            return "C12494"

        if isinstance(cmp, pf_533984002):
            return "C393945"

        if isinstance(cmp, B4B_ZR_SM4_TF):
            return "C145997"

        if isinstance(cmp, Capacitor):
            cmp.add_trait(has_defined_type_description("C"))
            cmp.add_trait(
                can_attach_to_footprint_via_pinmap(
                    {
                        "1": cmp.IFs.unnamed[0],
                        "2": cmp.IFs.unnamed[1],
                    }
                )
            )

            capacitors = {
                "C1525": Constant(100 * n),
                "C52923": Constant(1 * u),
                "C368809": Constant(4700 * n),
            }

            capacitance = cmp.capacitance
            for partno, resistance in capacitors.items():
                if (
                    isinstance(capacitance, Constant)
                    and capacitance.value == resistance.value
                ):
                    return partno
                if (
                    isinstance(capacitance, Range)
                    and resistance.value >= capacitance.min
                    and resistance.value <= capacitance.max
                ):
                    cmp.set_capacitance(capacitance)
                    return partno
                if isinstance(capacitance, TBD):
                    raise Exception(f"Capacitance is TBD for {cmp.get_full_name}")

            raise Exception(
                f"Could not find fitting capacitor for value: {capacitance.value} for {str(cmp.get_full_name).split('|')[2].split('>')[0]}"
            )

        if isinstance(cmp, ME6211C33M5G_N):
            return "C82942"

        # if isinstance(cmp, USB_Type_C_Receptacle_14_pin_Vertical):
        #    return "C168704"

        # ------------------------------------------
        if isinstance(cmp, USB_Type_C_Receptacle_24_pin):
            return "C134092"

        if isinstance(cmp, Resistor):
            resistance_param = cmp.get_trait(has_resistance).get_resistance()
            assert isinstance(resistance_param, Parameter)

            resistors = {
                "C137885": Constant(300),
                "C226726": Constant(5.1 * k),
                "C25741": Constant(100 * k),
                "C11702": Constant(1 * k),
                "C25744": Constant(10 * k),
            }

            for partno, resistance in resistors.items():
                if (
                    isinstance(resistance_param, Constant)
                    and resistance_param.value == resistance.value
                ):
                    return partno
                if (
                    isinstance(resistance_param, Range)
                    and resistance.value >= resistance_param.min
                    and resistance.value <= resistance_param.max
                ):
                    cmp.set_resistance(resistance)
                    return partno

            raise Exception(
                f"Could not find fitting resistor for value: {resistance_param}"
            )

        if isinstance(cmp, LED):
            cmp.add_trait(
                can_attach_to_footprint_via_pinmap(
                    {
                        "1": cmp.IFs.anode,
                        "2": cmp.IFs.cathode,
                    }
                )
            )

            return "C84256"

        if isinstance(cmp, MOSFET):
            cmp.add_trait(
                can_attach_to_footprint_via_pinmap(
                    {
                        "2": cmp.IFs.source,
                        "3": cmp.IFs.drain,
                        "1": cmp.IFs.gate,
                    }
                )
            )

            mosfets = {
                "C8545": (
                    MOSFET.ChannelType.N_CHANNEL,
                    MOSFET.SaturationType.ENHANCEMENT,
                ),
                "C8492": (
                    MOSFET.ChannelType.P_CHANNEL,
                    MOSFET.SaturationType.ENHANCEMENT,
                ),
            }

            for partno, (channel_type, sat_type) in mosfets.items():
                if cmp.channel_type == channel_type and cmp.saturation_type == sat_type:
                    return partno

            raise Exception(
                "Could not find fitting mosfet for: "
                f"{cmp.channel_type, cmp.saturation_type}"
            )

        return None

    partno = _find_partno()
    if partno is None:
        return
    lcsc.attach_footprint(cmp, partno)
