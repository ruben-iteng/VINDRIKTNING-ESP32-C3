from dataclasses import dataclass

import faebryk.library._F as F
from faebryk.core.core import Module


class FanController(Module):
    """
    Module containing the hardware needed to controll a fan
    - LED indicator
    - MOSFET power switch
    """

    @dataclass
    class _fancontroller_esphome_config(F.has_esphome_config.impl()):
        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            obj = self.get_obj()
            assert isinstance(obj, FanController), "This is not a FanController!"

            control_pin = F.is_esphome_bus.find_connected_bus(
                obj.IFs.control_input.IFs.signal
            )

            return {
                "fan": [
                    {
                        "platform": "speed",
                        "output": control_pin.get_trait(F.is_esphome_bus).get_bus_id(),
                    }
                ]
            }

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

        self.NODEs.flyback_protection_diode.PARAMs.forward_voltage.merge(
            F.Constant(1.1)
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

        self.NODEs.led.IFs.power.connect_via(
            self.NODEs.fan_power_switch, self.IFs.power_in
        )

        self.add_trait(F.can_bridge_defined(self.IFs.power_in, self.IFs.fan_output))

        self.esphome = self._fancontroller_esphome_config()
        self.add_trait(self.esphome)
