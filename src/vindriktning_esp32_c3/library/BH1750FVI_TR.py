import logging
from dataclasses import dataclass, field

from faebryk.core.core import Module, Parameter
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_designator_prefix_defined import (
    has_designator_prefix_defined,
)
from faebryk.library.has_esphome_config import (
    has_esphome_config,
    is_esphome_bus,
)
from faebryk.library.has_single_electric_reference_defined import (
    has_single_electric_reference_defined,
)
from faebryk.library.I2C import I2C
from faebryk.library.Resistor import Resistor
from faebryk.library.TBD import TBD
from faebryk.libs.units import k, n, u
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class BH1750FVI_TR(Module):
    @dataclass
    class _bh1750_esphome_config(has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, Constant
            ), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, BH1750FVI_TR)

            i2c = is_esphome_bus.find_connected_bus(obj.IFs.i2c)

            return {
                "sensor": [
                    {
                        "platform": "bh1750",
                        "name": "BH1750 Illuminance",
                        "address": "0x23",
                        "i2c_id": i2c.get_trait(is_esphome_bus).get_bus_id(),
                        "update_interval": f"{self.update_interval_s.value}s",
                    }
                ]
            }

    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            i2c_termination_resistors = times(2, lambda: Resistor(TBD()))
            decoupling_cap = Capacitor(
                capacitance=Constant(100 * n),
                rated_voltage=TBD(),
                temperature_coefficient=TBD(),
            )
            dvi_capacitor = Capacitor(
                capacitance=Constant(1 * u),
                rated_voltage=TBD(),
                temperature_coefficient=TBD(),
            )
            dvi_resistor = Resistor(Constant(1 * k))

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            power = ElectricPower()
            addr = ElectricLogic()
            dvi = ElectricLogic()
            ep = ElectricLogic()
            i2c = I2C()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.power.NODEs.hv,
                    "2": x.addr.NODEs.signal,
                    "3": x.power.NODEs.lv,
                    "4": x.i2c.NODEs.sda.NODEs.signal,
                    "5": x.dvi.NODEs.signal,
                    "6": x.i2c.NODEs.scl.NODEs.signal,
                    "7": x.ep.NODEs.signal,
                }
            )
        )

        self.IFs.i2c.terminate(
            (
                self.NODEs.i2c_termination_resistors[0],
                self.NODEs.i2c_termination_resistors[1],
            )
        )

        self.IFs.i2c.PARAMs.frequency.merge(
            I2C.define_max_frequency_capability(I2C.SpeedMode.fast_speed)
        )

        self.add_trait(has_designator_prefix_defined("U"))

        self.add_trait(
            has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/1811081611_ROHM-Semicon-BH1750FVI-TR_C78960.pdf"
            )
        )

        # internal connections
        ref = ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))
        ref.connect(self.IFs.power)

        self.IFs.power.decouple(self.NODEs.decoupling_cap)
        self.IFs.dvi.low_pass(self.NODEs.dvi_capacitor, self.NODEs.dvi_resistor)

        # self.IFs.i2c.add_trait(is_esphome_bus.impl()())
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
