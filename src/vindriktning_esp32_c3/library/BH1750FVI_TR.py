import logging
from dataclasses import dataclass, field

import faebryk.library._F as F
from faebryk.core.core import Module, Parameter
from faebryk.libs.units import k, u

logger = logging.getLogger(__name__)


class BH1750FVI_TR(Module):
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
            assert isinstance(obj, BH1750FVI_TR)

            i2c = F.is_esphome_bus.find_connected_bus(obj.IFs.i2c)

            return {
                "sensor": [
                    {
                        "platform": "bh1750",
                        "name": "BH1750 Illuminance",
                        "address": "0x23",
                        "i2c_id": i2c.get_trait(F.is_esphome_bus).get_bus_id(),
                        "update_interval": f"{self.update_interval_s.value}s",
                    }
                ]
            }

    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            dvi_capacitor = F.Capacitor()
            dvi_resistor = F.Resistor()

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            addr = F.ElectricLogic()
            dvi = F.ElectricLogic()
            ep = F.ElectricLogic()
            i2c = F.I2C()

        self.IFs = _IFs(self)

        self.NODEs.dvi_capacitor.PARAMs.capacitance.merge(1 * u)
        self.NODEs.dvi_resistor.PARAMs.resistance.merge(1 * k)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": x.power.IFs.hv,
                    "2": x.addr.IFs.signal,
                    "3": x.power.IFs.lv,
                    "4": x.i2c.IFs.sda.IFs.signal,
                    "5": x.dvi.IFs.signal,
                    "6": x.i2c.IFs.scl.IFs.signal,
                    "7": x.ep.IFs.signal,
                }
            )
        )

        self.IFs.i2c.terminate()

        self.IFs.i2c.PARAMs.frequency.merge(
            F.I2C.define_max_frequency_capability(F.I2C.SpeedMode.fast_speed)
        )

        self.add_trait(F.has_designator_prefix_defined("U"))

        self.add_trait(
            F.has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/1811081611_ROHM-Semicon-BH1750FVI-TR_C78960.pdf"
            )
        )

        # set constraints
        self.IFs.power.PARAMs.voltage.merge(F.Range(2.4, 3.6))

        # internal connections
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))
        ref.connect(self.IFs.power)

        self.IFs.power.get_trait(F.can_be_decoupled).decouple()  # TODO: 100nF
        # TODO: self.IFs.dvi.low_pass(self.IF.dvi_capacitor, self.IF.dvi_resistor)

        # self.IFs.i2c.add_trait(F.is_esphome_bus.impl()())
        self.esphome = self._bh1750_esphome_config()
        self.add_trait(self.esphome)

    def set_address(self, addr: int):
        raise NotImplementedError()
        # ADDR = ‘H’ ( ADDR ≧ 0.7VCC ) “1011100“
        # ADDR = 'L' ( ADDR ≦ 0.3VCC ) “0100011“
        ...
        # assert addr < (1 << len(self.IFs.e))

        # for i, e in enumerate(self.IFs.e):
        #    e.set(addr & (1 << i) != 0)
