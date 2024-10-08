import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import Quantity
from faebryk.libs.util import cast_assert, times


class DigitalLED(Module):
    """
    Create a string of WS2812B RGBW LEDs with optional signal level translator
    """

    class _esphome_config(F.has_esphome_config.impl()):
        def get_config(self) -> dict:
            obj = self.get_obj(DigitalLED)
            val = cast_assert(F.Constant, obj.max_refresh_rate.get_most_narrow())

            gpio = F.is_esphome_bus.find_connected_bus(obj.data_in)

            return {
                "sensor": [
                    {
                        "platform": "esp32_rmt_led_strip",
                        "name": "F.LED string",
                        "rgb_order": "GRB",
                        "pin": gpio.get_trait(F.is_esphome_bus).get_bus_id(),
                        "num_leds": len(obj.leds),
                        "rmt_channel": 0,
                        "chipset": "SK6812",
                        "is_rgbw": False,
                        "max_refresh_rate": f"{val.value}s",
                    }
                ]
            }

        def is_implemented(self):
            return (
                isinstance(
                    self.get_obj(DigitalLED).max_refresh_rate.get_most_narrow(),
                    F.Constant,
                )
                and super().is_implemented()
            )

    esphome_config: _esphome_config

    class DecoupledDigitalLED[T: Module](Module):
        def __init__(self, led_class: type[T]):
            super().__init__()
            self._led_class = led_class

        data_in: F.ElectricLogic
        data_out: F.ElectricLogic
        power: F.ElectricPower

        @L.rt_field
        def led(self):
            return self._led_class()

        def __preinit__(self):
            self.data_in.connect_via(self.led, self.data_out)

            self.power.connect(self.led.power)

        @L.rt_field
        def single_electric_reference(self):
            return F.has_single_electric_reference_defined(
                F.ElectricLogic.connect_all_module_references(self)
            )

        @L.rt_field
        def can_bridge(self):
            return F.can_bridge_defined(self.data_in, self.data_out)

    def __init__(self, pixels: int, buffered: bool = False):
        super().__init__()
        self._pixels = pixels
        self._buffered = buffered

    data_in: F.ElectricLogic
    power: F.ElectricPower
    power_data: F.ElectricPower
    max_refresh_rate: F.TBD[Quantity]

    @L.rt_field
    def leds(self):
        return times(
            self._pixels, lambda: self.DecoupledDigitalLED(F.XL_3528RGBW_WS2812B)
        )

    def __preinit__(self):
        # connect power
        for led in self.leds:
            led.power.connect(self.power)

        if self._buffered:
            buffer = self.add(F.TXS0102DCUR())

            self.data_in.connect(buffer.shifters[0].io_a)
            buffer.shifters[0].io_b.connect_via(self.leds)

            buffer.n_oe.set(True)
            buffer.voltage_a_power.connect(self.power_data)
            buffer.voltage_b_power.connect(self.power)
            ref = self.power_data
        else:
            self.power_data.connect(self.power)
            self.data_in.connect_via(self.leds)
            ref = self.power

        self.data_in.reference.connect(ref)
