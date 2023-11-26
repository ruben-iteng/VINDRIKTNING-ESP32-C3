from faebryk.core.core import Module, Parameter
from dataclasses import dataclass, field
from faebryk.libs.units import m
from faebryk.library.Constant import Constant
from faebryk.library.Range import Range
from faebryk.library.TBD import TBD
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_esphome_config import has_esphome_config, is_esphome_bus
from faebryk.library.has_single_electric_reference import has_single_electric_reference
from faebryk.library.UART_Base import UART_Base
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF


class PM1006(Module):
    """
    Infrared LED particle sensor module PM1006 adopts the principle of optical scattering to detect the variation trend of particle (size between 0.3μm to 10μm) concentration in the air. There is an infrared light-emitting diode and an optoelectronic sensor built-in PM1006, and light rays from the light-emitting diode will be reflected when pass through the particle. The optoelectronic sensor can show the concentration of particle in the air by detecting the intensity of reflected light. Sensor can output measuring value by pulse or UART signal.
    """

    @dataclass
    class _pm1006_esphome_config(has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, Constant
            ), "No update interval set!"

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
                "sensor": [{
                    "platform": "pm1006",
                    "update_interval": f"{self.update_interval_s.value}s",
                    "uart_id": uart_cfg["id"],
                }]
            }

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

        self.esphome = self._pm1006_esphome_config()
        self.add_trait(self.esphome)
        # ---------------------------------------------------------------------

        self.IFs.power.add_constraint(
            ElectricPower.ConstraintVoltage(Range.from_center(5, 0.2)),
            ElectricPower.ConstraintCurrent(Constant(30 * m)),
        )

        self.IFs.data.get_trait(
            has_single_electric_reference
        ).get_reference().add_constraint(
            ElectricPower.ConstraintVoltage(Constant(4.5)),
        )

        self.NODEs.connector.IFs.pin[3].connect(self.IFs.power.NODEs.lv)
        self.NODEs.connector.IFs.pin[2].connect(self.IFs.power.NODEs.hv)
        self.NODEs.connector.IFs.pin[1].connect(self.IFs.data.NODEs.tx.NODEs.signal)
        self.NODEs.connector.IFs.pin[0].connect(self.IFs.data.NODEs.rx.NODEs.signal)

        self.IFs.data.set_baud(Constant(9600))
