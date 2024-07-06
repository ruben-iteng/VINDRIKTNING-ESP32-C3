import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.libs.brightness import TypicalLuminousIntensity


class FanController(Module):
    """
    Module containing the hardware needed to controll a fan
    - LED indicator
    - MOSFET power switch
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_in = F.ElectricPower()
            control_input = F.ElectricLogic()
            fan_output = F.ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            led = F.PoweredLED()
            fan_power_switch = F.PowerSwitchMOSFET(lowside=True, normally_closed=False)
            flyback_protection_diode = F.Diode()

        self.NODEs = _NODEs(self)

        self.NODEs.flyback_protection_diode.PARAMs.forward_voltage.merge(F.Constant(40))
        self.NODEs.led.NODEs.led.PARAMs.color.merge(F.LED.Color.RED)
        self.NODEs.led.NODEs.led.PARAMs.brightness.merge(
            TypicalLuminousIntensity.APPLICATION_LED_STANDBY.value.value
        )

        # internal connections
        self.NODEs.fan_power_switch.IFs.logic_in.connect(self.IFs.control_input)
        self.IFs.fan_output.connect_via(self.NODEs.fan_power_switch, self.IFs.power_in)

        self.IFs.fan_output.IFs.hv.connect(
            self.NODEs.flyback_protection_diode.IFs.anode
        )
        self.IFs.fan_output.IFs.lv.connect(
            self.NODEs.flyback_protection_diode.IFs.cathode
        )

        self.IFs.power_in.IFs.hv.connect_via(
            [self.NODEs.led, self.NODEs.fan_power_switch], self.IFs.power_in.IFs.lv
        )

        self.add_trait(F.can_bridge_defined(self.IFs.power_in, self.IFs.fan_output))

        self.add_trait(
            F.has_pcb_layout_defined(
                LayoutTypeHierarchy(
                    layouts=[
                        LayoutTypeHierarchy.Level(
                            mod_type=F.PoweredLED,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (0, 5.5, 90, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                            # TODO: Fix children_layout
                            # children_layout=LayoutTypeHierarchy(
                            #    layouts=[
                            #        LayoutTypeHierarchy.Level(
                            #            mod_type=F.LED,
                            #            layout=LayoutAbsolute(
                            #                F.has_pcb_position.Point(
                            #                    (
                            #                        0,
                            #                        0,
                            #                        180,
                            #                        F.has_pcb_position.layer_type.NONE,
                            #                    )
                            #                )
                            #            ),
                            #        ),
                            #        LayoutTypeHierarchy.Level(
                            #            mod_type=F.Resistor,
                            #            layout=LayoutAbsolute(
                            #                F.has_pcb_position.Point(
                            #                    (
                            #                        0,
                            #                        3,
                            #                        270,
                            #                        F.has_pcb_position.layer_type.NONE,
                            #                    )
                            #                )
                            #            ),
                            #        ),
                            #    ]
                            # ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=F.PowerSwitchMOSFET,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (0, 0, 0, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                            # TODO: Fix children_layout
                            # children_layout=LayoutTypeHierarchy(
                            #    layouts=[
                            #        LayoutTypeHierarchy.Level(
                            #            mod_type=F.Resistor,
                            #            layout=LayoutAbsolute(
                            #                F.has_pcb_position.Point(
                            #                    (
                            #                        0,
                            #                        -2.5,
                            #                        180,
                            #                        F.has_pcb_position.layer_type.NONE,
                            #                    )
                            #                )
                            #            ),
                            #        ),
                            #        LayoutTypeHierarchy.Level(
                            #            mod_type=F.MOSFET,
                            #            layout=LayoutAbsolute(
                            #                F.has_pcb_position.Point(
                            #                    (
                            #                        0,
                            #                        2.5,
                            #                        0,
                            #                        F.has_pcb_position.layer_type.NONE,
                            #                    )
                            #                )
                            #            ),
                            #        ),
                            #    ]
                            # ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=F.Diode,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (0, 3, 90, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                    ]
                )
            )
        )
