from faebryk.core.core import Module
from faebryk.core.util import connect_all_interfaces
from faebryk.library.Constant import Constant
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.Resistor import Resistor
from vindriktning_esp32_c3.library.USB_Type_C_Receptacle_14_pin_Vertical import (
    USB_Type_C_Receptacle_14_pin_Vertical,
)
from faebryk.libs.units import k
from faebryk.libs.util import times


class USB_C_PSU_Vertical(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_out = ElectricPower()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            usb = USB_Type_C_Receptacle_14_pin_Vertical()
            configuration_resistors = times(2, lambda: Resistor(Constant(5.1 * k)))

        self.NODEs = _NODEs(self)

        connect_all_interfaces(
            list(self.NODEs.usb.IFs.vbus + [self.IFs.power_out.NODEs.hv])
        )
        connect_all_interfaces(
            list(self.NODEs.usb.IFs.gnd + [self.IFs.power_out.NODEs.lv])
        )

        # configure as ufp with 5V@max3A
        self.NODEs.usb.IFs.cc1.connect_via(
            self.NODEs.configuration_resistors[0], self.IFs.power_out.NODEs.lv
        )
        self.NODEs.usb.IFs.cc2.connect_via(
            self.NODEs.configuration_resistors[1], self.IFs.power_out.NODEs.lv
        )
