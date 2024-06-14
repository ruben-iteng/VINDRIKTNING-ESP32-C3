import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import connect_all_interfaces
from faebryk.libs.units import M, k, n, u
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.USB_Type_C_Receptacle_14_pin_Vertical import (
    USB_Type_C_Receptacle_14_pin_Vertical,
)
from vindriktning_esp32_c3.library.USBLC6_2P6 import USBLC6_2P6


class USB_C_PSU_Vertical(Module):
    class USB_2_0_ESD(Module):
        """
        USB 2.0 ESD protection
        """

        def __init__(self) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                usb_in = F.USB2_0()
                usb_out = F.USB2_0()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                esd = USBLC6_2P6()

            self.NODEs = _NODEs(self)

            # connect
            self.IFs.usb_in.connect_via(self.NODEs.esd, self.IFs.usb_out)

            # Add bridge trait
            self.add_trait(F.can_bridge_defined(self.IFs.usb_in, self.IFs.usb_out))

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_out = F.ElectricPower()
            usb = F.USB2_0()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            # TODO add fuse
            usb_connector = USB_Type_C_Receptacle_14_pin_Vertical()
            configuration_resistors = times(2, F.Resistor)
            gnd_resistor = F.Resistor()
            gnd_capacitor = F.Capacitor()
            esd_capacitor = F.Capacitor()
            esd = USBLC6_2P6()

        self.NODEs = _NODEs(self)

        self.NODEs.gnd_capacitor.PARAMs.capacitance.merge(100 * n)
        self.NODEs.esd_capacitor.PARAMs.capacitance.merge(1 * u)
        self.NODEs.gnd_resistor.PARAMs.resistance.merge(1 * M)
        for res in self.NODEs.configuration_resistors:
            res.PARAMs.resistance.merge(5.1 * k)

        # alliases
        gnd = self.IFs.power_out.IFs.lv

        connect_all_interfaces(
            list(
                self.NODEs.usb_connector.IFs.vbus
                + [
                    self.IFs.power_out.IFs.hv,
                    self.NODEs.esd.IFs.usb.IFs.buspower.IFs.hv,
                ]
            )
        )
        connect_all_interfaces(
            list(
                self.NODEs.usb_connector.IFs.gnd
                + [
                    gnd,
                    self.NODEs.esd.IFs.usb.IFs.buspower.IFs.lv,
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

        self.NODEs.esd.IFs.usb.IFs.buspower.get_trait(
            F.can_be_decoupled
        ).decouple()  # TODO: use esd_capacitor

        # EMI shielding
        self.NODEs.usb_connector.IFs.shield.connect_via(self.NODEs.gnd_resistor, gnd)
        self.NODEs.usb_connector.IFs.shield.connect_via(self.NODEs.gnd_capacitor, gnd)
