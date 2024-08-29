import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P


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

    led: F.PoweredLED
    fan_power_switch = L.f_field(F.PowerSwitchMOSFET)(
        lowside=True, normally_closed=False
    )
    flyback_protection_diode: F.Diode

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.power_in, self.fan_output)

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.fan_power_switch.logic_in.connect(self.control_input)
        self.fan_output.connect_via(self.fan_power_switch, self.power_in)

        self.fan_output.hv.connect(self.flyback_protection_diode.anode)
        self.fan_output.lv.connect(self.flyback_protection_diode.cathode)

        self.led.power.connect_via(self.fan_power_switch, self.power_in)

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.flyback_protection_diode.forward_voltage.merge(1.1 * P.V)

    class _fancontroller_esphome_config(F.has_esphome_config.impl()):
        def get_config(self) -> dict:
            obj = self.get_obj()
            assert isinstance(obj, FanController), "This is not a FanController!"

            control_pin = F.is_esphome_bus.find_connected_bus(obj.control_input.signal)

            return {
                "fan": [
                    {
                        "platform": "speed",
                        "output": control_pin.get_trait(F.is_esphome_bus).get_bus_id(),
                    }
                ]
            }

    esphome_config: _fancontroller_esphome_config
