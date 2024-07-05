import faebryk.library._F as F
from faebryk.core.core import Module, Parameter
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.TXS0102DCUR import TXS0102DCUR
from vindriktning_esp32_c3.library.XL_3528RGBW_WS2812B import XL_3528RGBW_WS2812B


class DigitalLED(Module):
    """
    Create a string of WS2812B RGBW LEDs with optional signal level translator
    """

    class _digitalLED_esphome_config(F.has_esphome_config.impl()):
        def get_config(self) -> dict:
            obj = self.get_obj()
            assert isinstance(obj, DigitalLED)
            assert isinstance(
                obj.max_refresh_rate_hz, F.Constant
            ), "No update interval set!"

            gpio = F.is_esphome_bus.find_connected_bus(obj.IFs.data_in)

            return {
                "sensor": [
                    {
                        "platform": "esp32_rmt_led_strip",
                        "name": "F.LED string",
                        "rgb_order": "GRB",
                        "pin": gpio.get_trait(F.is_esphome_bus).get_bus_id(),
                        "num_leds": len(obj.NODEs.leds),
                        "rmt_channel": 0,
                        "chipset": "SK6812",
                        "is_rgbw": False,
                        "max_refresh_rate": f"{obj.max_refresh_rate_hz.value}s",
                    }
                ]
            }

    class DecoupledDigitalLED(Module):
        def __init__(self, led_class) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                data_in = F.ElectricLogic()
                data_out = F.ElectricLogic()
                power = F.ElectricPower()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                led = led_class()

            self.NODEs = _NODEs(self)

            self.IFs.power.get_trait(F.can_be_decoupled).decouple()
            self.IFs.data_in.connect_via(self.NODEs.led, self.IFs.data_out)

            self.IFs.power.connect(self.NODEs.led.IFs.power)

            # connect all logic references
            ref = F.ElectricLogic.connect_all_module_references(self)
            self.add_trait(F.has_single_electric_reference_defined(ref))

            # Add bridge trait
            self.add_trait(F.can_bridge_defined(self.IFs.data_in, self.IFs.data_out))

    def __init__(self, pixels: Parameter, buffered: bool = True) -> None:
        super().__init__()

        assert isinstance(pixels, F.Constant)

        self.pixels = pixels
        self.buffered = buffered

        class _IFs(Module.IFS()):
            data_in = F.ElectricLogic()
            power = F.ElectricPower()
            if buffered:
                power_data = F.ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            if buffered:
                buffer = TXS0102DCUR()
            leds = times(
                self.pixels.value, lambda: self.DecoupledDigitalLED(XL_3528RGBW_WS2812B)
            )

        self.NODEs = _NODEs(self)

        di = F.ElectricLogic()

        # connect power
        for led in self.NODEs.leds:
            led.IFs.power.connect(self.IFs.power)

        # connect all F.LEDs in series
        di.connect_via(self.NODEs.leds)

        # put buffer in between if needed
        if buffered:
            self.IFs.data_in.connect_via(self.NODEs.buffer.NODEs.shifters[0], di)
            self.NODEs.buffer.IFs.voltage_a_power.connect(self.IFs.power_data)
            self.NODEs.buffer.IFs.voltage_b_power.connect(self.IFs.power)
        else:
            self.IFs.data_in.connect(di)

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        # esphome
        self.esphome = self._digitalLED_esphome_config()
        self.add_trait(self.esphome)

        self.max_refresh_rate_hz: Parameter = F.TBD()
