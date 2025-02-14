import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P

from vindriktning.components.FanConnector import FanConnector


class FanController(Module):
    """
    Module containing the hardware needed to controll a fan
    - LED indicator
    - MOSFET power switch
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power_in: F.ElectricPower
    control_input: F.ElectricLogic
    fan_output: F.ElectricPower
    fan_connector: FanConnector

    led: F.PoweredLED
    fan_power_switch = L.f_field(F.PowerSwitchMOSFET)(
        lowside=True, normally_closed=False
    )
    flyback_protection_diode: F.Diode

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.fan_power_switch.logic_in.connect(self.control_input)
        self.fan_connector.power.connect_via(self.fan_power_switch, self.power_in)

        self.fan_connector.power.lv.connect_via(
            self.flyback_protection_diode, self.fan_connector.power.hv
        )

        self.led.power.connect_via(self.fan_power_switch, self.power_in)

        # ------------------------------------
        #          parametrization
        # ------------------------------------

        # Assume the body diode forward voltage of the fan power switch is higher than 0.5V
        self.flyback_protection_diode.forward_voltage.constrain_le(0.5 * P.V)

    class _fancontroller_esphome_config(F.has_esphome_config.impl()):
        def get_config(self) -> dict:
            obj = self.get_obj(FanController)
            control_pin = F.is_esphome_bus.find_connected_bus(obj.control_input)

            return {
                "fan": [
                    {
                        "platform": "speed",
                        "output": control_pin.get_trait(F.is_esphome_bus).get_bus_id(),
                    }
                ]
            }

    esphome_config: _fancontroller_esphome_config
