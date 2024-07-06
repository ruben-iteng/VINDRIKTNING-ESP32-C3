from faebryk.core.core import Module
from faebryk.core.util import connect_all_interfaces
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.library.can_be_decoupled import can_be_decoupled
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Capacitor import Capacitor
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.Fuse import Fuse
from faebryk.library.has_pcb_layout_defined import has_pcb_layout_defined
from faebryk.library.has_pcb_position import has_pcb_position
from faebryk.library.Resistor import Resistor
from faebryk.library.USB2_0 import USB2_0
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
            # TODO add fuse
            usb_connector = USB_Type_C_Receptacle_14_pin_Vertical()
            configuration_resistors = times(2, Resistor)
            gnd_resistor = Resistor()
            gnd_capacitor = Capacitor()
            esd_capacitor = Capacitor()
            esd = USBLC6_2P6()

        self.NODEs = _NODEs(self)

        self.NODEs.gnd_capacitor.PARAMs.capacitance.merge(100 * n)
        self.NODEs.gnd_capacitor.PARAMs.rated_voltage.merge(1000)
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
            can_be_decoupled
        ).decouple()  # TODO: use esd_capacitor

        # EMI shielding
        self.NODEs.usb_connector.IFs.shield.connect_via(self.NODEs.gnd_resistor, gnd)
        self.NODEs.usb_connector.IFs.shield.connect_via(self.NODEs.gnd_capacitor, gnd)

        # PCB layout
        self.NODEs.gnd_resistor.add_trait(
            has_pcb_layout_defined(
                layout=LayoutAbsolute(
                    has_pcb_position.Point(
                        (5.5, 0, 90, has_pcb_position.layer_type.NONE)
                    )
                ),
            )
        )
        self.NODEs.gnd_capacitor.add_trait(
            has_pcb_layout_defined(
                layout=LayoutAbsolute(
                    has_pcb_position.Point(
                        (-5.5, 0, 90, has_pcb_position.layer_type.NONE)
                    )
                ),
            )
        )
        self.NODEs.esd_capacitor.add_trait(
            has_pcb_layout_defined(
                layout=LayoutAbsolute(
                    has_pcb_position.Point(
                        (-12, -9.5, 90, has_pcb_position.layer_type.NONE)
                    )
                ),
            )
        )

        self.add_trait(
            has_pcb_layout_defined(
                LayoutTypeHierarchy(
                    layouts=[
                        LayoutTypeHierarchy.Level(
                            mod_type=USB_Type_C_Receptacle_14_pin_Vertical,
                            layout=LayoutAbsolute(
                                has_pcb_position.Point(
                                    (0, 0.2, 0, has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=USBLC6_2P6,
                            layout=LayoutAbsolute(
                                has_pcb_position.Point(
                                    (-5, -8.5, 0, has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=Fuse,
                            layout=LayoutAbsolute(
                                has_pcb_position.Point(
                                    (
                                        2.5,
                                        -4.75,
                                        90,
                                        has_pcb_position.layer_type.NONE,
                                    )
                                )
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=Resistor,
                            layout=LayoutExtrude(
                                base=has_pcb_position.Point(
                                    (
                                        -0.5,
                                        -4.5,
                                        90,
                                        has_pcb_position.layer_type.NONE,
                                    )
                                ),
                                vector=(0, 1, 0),
                            ),
                        ),
                    ]
                )
            )
        )
