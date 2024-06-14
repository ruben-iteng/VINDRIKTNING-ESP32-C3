from dataclasses import dataclass, field

import faebryk.library._F as F
from faebryk.core.core import Module, Parameter
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF


class PM1006(Module):
    """
    Infrared F.LED particle sensor module PM1006
    adopts the principle of optical scattering to
    detect the variation trend of particle
    (size between 0.3μm to 10μm) concentration in
    the air. There is an infrared light-emitting
    diode and an optoelectronic sensor built-in
    PM1006, and light rays from the light-emitting
    diode will be reflected when pass through
    the particle. The optoelectronic sensor can
    show the concentration of particle in the air
    by detecting the intensity of reflected light.
    Sensor can output measuring value by pulse
    or UART signal.
    """

    @dataclass
    class _pm1006_esphome_config(F.has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=F.TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, F.Constant
            ), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, PM1006), "This is not an PM1006!"

            uart = F.is_esphome_bus.find_connected_bus(obj.IFs.data)

            return {
                "sensor": [
                    {
                        "platform": "pm1006",
                        "update_interval": f"{self.update_interval_s.value}s",
                        "uart_id": uart.get_trait(F.is_esphome_bus).get_bus_id(),
                    }
                ]
            }

    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            data = F.UART_Base()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            connector = B4B_ZR_SM4_TF()

        self.NODEs = _NODEs(self)
        # ---------------------------------------------------------------------

        self.add_trait(
            F.has_datasheet_defined(
                "http://www.jdscompany.co.kr/download.asp?gubun=07&filename=PM1006_F.LED_PARTICLE_SENSOR_MODULE_SPECIFICATIONS.pdf"
            )
        )

        self.esphome = self._pm1006_esphome_config()
        self.add_trait(self.esphome)
        # ---------------------------------------------------------------------

        self.IFs.power.PARAMs.voltage.merge(F.Range.from_center(5, 0.2))
        # self.IFs.power.PARAMs.current_sink.merge(F.Constant(30 * m))

        # TODO fix with UART_Voltage_Dropper
        # self.IFs.data.get_trait(
        #    has_single_electric_reference
        # ).get_reference().add_constraint(
        #    F.ElectricPower.ConstraintVoltage(F.Constant(4.5)),
        # )

        self.NODEs.connector.IFs.pin[3].connect(self.IFs.power.IFs.lv)
        self.NODEs.connector.IFs.pin[2].connect(self.IFs.power.IFs.hv)
        self.NODEs.connector.IFs.pin[1].connect(self.IFs.data.IFs.tx.IFs.signal)
        self.NODEs.connector.IFs.pin[0].connect(self.IFs.data.IFs.rx.IFs.signal)

        self.IFs.data.PARAMs.baud.merge(F.Constant(9600))
