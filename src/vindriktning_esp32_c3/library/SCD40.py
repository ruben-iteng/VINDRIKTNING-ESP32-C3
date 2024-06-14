from dataclasses import dataclass, field

import faebryk.library._F as F
from faebryk.core.core import Module, Parameter


class SCD40(Module):
    @dataclass
    class _bh1750_esphome_config(F.has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=F.TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, F.Constant
            ), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, SCD40)

            i2c = F.is_esphome_bus.find_connected_bus(obj.IFs.i2c)

            return {
                "sensor": [
                    {
                        "platform": "scd4x",
                        "co2": {
                            "name": "CO2",
                        },
                        "temperature": {
                            "name": "Moving Temperature",
                        },
                        "humidity": {
                            "name": "Humidity",
                        },
                        "address": 0x62,
                        "i2c_id": i2c.get_trait(F.is_esphome_bus).get_bus_id(),
                        "update_interval": f"{self.update_interval_s.value}s",
                    }
                ]
            }

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            i2c = F.I2C()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "6": x.power.IFs.lv,
                    "7": x.power.IFs.hv,
                    "9": x.i2c.IFs.scl.IFs.signal,
                    "10": x.i2c.IFs.sda.IFs.signal,
                    "19": x.power.IFs.hv,
                    "20": x.power.IFs.lv,
                    "21": x.power.IFs.lv,
                    "22": x.power.IFs.lv,
                    "23": x.power.IFs.lv,
                    "24": x.power.IFs.lv,
                }
            )
        )

        self.add_trait(F.has_designator_prefix_defined("U"))
        self.IFs.i2c.PARAMs.frequency.merge(
            F.I2C.define_max_frequency_capability(F.I2C.SpeedMode.fast_speed)
        )

        # self.IFs.i2c.add_trait(F.is_esphome_bus.impl()())
        self.esphome = self._bh1750_esphome_config()
        self.add_trait(self.esphome)
