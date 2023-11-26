import logging

from faebryk.core.core import Module
from faebryk.library.Constant import Constant
from vindriktning_esp32_c3.library.Fan import Fan
from vindriktning_esp32_c3.library.PM1006 import PM1006
from vindriktning_esp32_c3.vindriktning_esp32_c3_base import Vindriktning_ESP32_C3

logger = logging.getLogger(__name__)


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
