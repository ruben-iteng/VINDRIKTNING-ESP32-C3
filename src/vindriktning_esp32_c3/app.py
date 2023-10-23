import logging
from abc import abstractmethod
from faebryk.core.core import Module, ModuleTrait, Parameter
from dataclasses import dataclass, field
from faebryk.libs.units import m
from faebryk.library.Constant import Constant
from faebryk.library.TBD import TBD
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_esphome_config import has_esphome_config, is_esphome_bus
from faebryk.library.has_single_electric_reference import has_single_electric_reference
from faebryk.library.UART_Base import UART_Base
from vindriktning_esp32_c3.vindriktning_esp32_c3_base import Vindriktning_ESP32_C3
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF

logger = logging.getLogger(__name__)


@dataclass
class _pm1006_esphome_config(has_esphome_config.impl()):
    update_interval_s: Parameter = field(default_factory=TBD)

    def __post_init__(self) -> None:
        super().__init__()

    def get_config(self) -> dict:
        assert isinstance(self.update_interval_s, Constant), "No update interval set!"

        obj = self.get_obj()
        assert isinstance(obj, PM1006), "This is not an PM1006!"

        uart_candidates = {
            mif
            for mif in obj.IFs.data.get_direct_connections()
            if mif.has_trait(is_esphome_bus) and mif.has_trait(has_esphome_config)
        }

        assert len(uart_candidates) == 1, f"Expected 1 UART, got {uart_candidates}"
        uart = uart_candidates.pop()
        uart_cfg = uart.get_trait(has_esphome_config).get_config()["uart"][0]

        return {
            "sensor": {
                "platform": "pm1006",
                "update_interval": f"{self.update_interval_s.value}s",
                "uart_id": uart_cfg["id"],
            }
        }


class PM1006(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = ElectricPower()
            data = UART_Base()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            connector = B4B_ZR_SM4_TF()

        self.NODEs = _NODEs(self)
        # ---------------------------------------------------------------------

        self.add_trait(
            has_datasheet_defined(
                "http://www.jdscompany.co.kr/download.asp?gubun=07&filename=PM1006_LED_PARTICLE_SENSOR_MODULE_SPECIFICATIONS.pdf"
            )
        )

        self.esphome = _pm1006_esphome_config()
        self.add_trait(self.esphome)
        # ---------------------------------------------------------------------

        self.IFs.power.add_constraint(
            ElectricPower.ConstraintConsumeVoltage(
                Constant(5), tolerance=Constant(0.2)
            ),
            ElectricPower.ConstraintConsumeCurrent(Constant(30 * m)),
        )

        self.IFs.data.get_trait(
            has_single_electric_reference
        ).get_reference().add_constraint(
            ElectricPower.ConstraintConsumeVoltage(Constant(4.5)),
        )

        self.NODEs.connector.IFs.pin[3].connect(self.IFs.power.NODEs.lv)
        self.NODEs.connector.IFs.pin[2].connect(self.IFs.power.NODEs.hv)
        self.NODEs.connector.IFs.pin[1].connect(self.IFs.data.NODEs.tx.NODEs.signal)
        self.NODEs.connector.IFs.pin[0].connect(self.IFs.data.NODEs.rx.NODEs.signal)

        self.IFs.data.set_baud(Constant(9600))


class Fan(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = ElectricPower()
            # tacho

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            ...
            # connector = some 2 pin thing

        self.NODEs = _NODEs(self)

        self.IFs.power.add_constraint(
            ElectricPower.ConstraintConsumeVoltage(Constant(5)),
            ElectricPower.ConstraintConsumeCurrent(Constant(40 * m)),
        )


class SmartVindrikting(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            ...

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            mcu_pcb = Vindriktning_ESP32_C3()
            particulate_sensor = PM1006()
            fan = Fan()

        self.NODEs = _NODEs(self)

        self.NODEs.particulate_sensor.esphome.update_interval_s = Constant(20)

        # TODO connect
        self.NODEs.particulate_sensor.IFs.data.connect(
            self.NODEs.mcu_pcb.NODEs.mcu.IFs.serial[1]
        )
