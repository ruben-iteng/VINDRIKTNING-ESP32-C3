import imp
from faebryk.core.core import Module
from faebryk.core.util import connect_all_interfaces
from faebryk.library.Constant import Constant
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.Resistor import Resistor
from faebryk.library.Capacitor import Capacitor
from vindriktning_esp32_c3.library.USB_Type_C_Receptacle_14_pin_Vertical import (
    USB_Type_C_Receptacle_14_pin_Vertical,
)
from vindriktning_esp32_c3.library.USBLC6_2P6 import USBLC6_2P6

from faebryk.libs.units import k, M, n, u
from faebryk.libs.util import times
from faebryk.library.USB2_0 import USB2_0
from faebryk.library.can_bridge_defined import can_bridge_defined


class USB_C_PSU_Vertical(Module):
    class USB_2_0_ESD(Module):
        """
        USB 2.0 ESD protection
        """

        def __init__(self) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                usb_in = USB2_0()
                usb_out = USB2_0()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                esd = USBLC6_2P6()

            self.NODEs = _NODEs(self)

            # connect
            self.IFs.usb_in.connect_via(self.NODEs.esd, self.IFs.usb_out)

            # Add bridge trait
            self.add_trait(can_bridge_defined(self.IFs.usb_in, self.IFs.usb_out))

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_out = ElectricPower()
            usb = USB2_0()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            usb_connector = USB_Type_C_Receptacle_14_pin_Vertical()
            configuration_resistors = times(2, lambda: Resistor(Constant(5.1 * k)))
            gnd_resistor = Resistor(Constant(1 * M))
            gnd_capacitor = Capacitor(Constant(100 * n))
            esd_capacitor = Capacitor(Constant(1 * u))
            esd = USBLC6_2P6()

        self.NODEs = _NODEs(self)

        # alliases
        gnd = self.IFs.power_out.NODEs.lv

        connect_all_interfaces(
            list(
                self.NODEs.usb_connector.IFs.vbus
                + [
                    self.IFs.power_out.NODEs.hv,
                    self.NODEs.esd.IFs.usb.NODEs.buspower.NODEs.hv,
                ]
            )
        )
        connect_all_interfaces(
            list(
                self.NODEs.usb_connector.IFs.gnd
                + [
                    gnd,
                    self.NODEs.esd.IFs.usb.NODEs.buspower.NODEs.lv,
                ]
            )
        )
        connect_all_interfaces(
            [self.NODEs.usb_connector.IFs.usb, self.IFs.usb, self.NODEs.esd.IFs.usb]
        )

        # configure as ufp with 5V@max3A
        self.NODEs.usb_connector.IFs.cc1.connect_via(
            self.NODEs.configuration_resistors[0], gnd
        )
        self.NODEs.usb_connector.IFs.cc2.connect_via(
            self.NODEs.configuration_resistors[1], gnd
        )

        self.NODEs.esd.IFs.usb.NODEs.buspower.decouple(self.NODEs.esd_capacitor)

        # EMI shielding
        self.NODEs.usb_connector.IFs.shield.connect_via(self.NODEs.gnd_resistor, gnd)
        self.NODEs.usb_connector.IFs.shield.connect_via(self.NODEs.gnd_capacitor, gnd)
