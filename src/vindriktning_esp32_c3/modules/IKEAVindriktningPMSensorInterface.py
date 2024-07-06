import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002
from vindriktning_esp32_c3.library.TXS0102DCUR import TXS0102DCUR
from vindriktning_esp32_c3.library.TXS0102DCUR_UART import TXS0102DCUR_UART
from vindriktning_esp32_c3.modules.FanConnector import FanConnector
from vindriktning_esp32_c3.modules.FanController import FanController
from vindriktning_esp32_c3.modules.PM1006Connector import PM1006Connector


class IKEAVindriktningPMSensorInterface(Module):
    """
    Module containing the hardware needed to connect to the fan and PM sensor
    in the IKEA VINDRIKTNING
      - Controllable FAN
        - Fan LED indicator
      - Level shifted UART
    """

    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            power_data = F.ElectricPower()
            fan_enable = F.ElectricLogic()
            uart = F.UART_Base()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            fan_controller = FanController()
            fan_connector = FanConnector()
            pm_sensor_level_shifter = TXS0102DCUR_UART()
            pm_sensor_connector = PM1006Connector()

        self.NODEs = _NODEs(self)

        self.IFs.power.PARAMs.voltage.merge(F.Range.from_center(5, 0.2))
        self.IFs.power_data.PARAMs.voltage.merge(F.Constant(3.3))

        # fan
        self.IFs.power.connect_via(
            self.NODEs.fan_controller, self.NODEs.fan_connector.IFs.power
        )
        self.NODEs.fan_controller.IFs.control_input.connect(self.IFs.fan_enable)

        # pm1006
        self.IFs.power.connect(self.NODEs.pm_sensor_level_shifter.IFs.voltage_b_power)
        self.IFs.power_data.connect(
            self.NODEs.pm_sensor_level_shifter.IFs.voltage_a_power
        )

        # TODO: connect shallow
        # self.IFs.uart.connect_via(
        #    self.NODEs.pm_sensor_level_shifter,
        #    self.NODEs.pm_sensor_connector.IFs.data,
        #    linkcls=F.Logic,
        # )

        self.add_trait(
            F.has_pcb_layout_defined(
                LayoutTypeHierarchy(
                    layouts=[
                        LayoutTypeHierarchy.Level(
                            mod_type=FanController,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (2.5, 27.5, 0, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=pf_533984002,  # FanConnector,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (2, 23, 180, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=TXS0102DCUR,  # TXS0102DCUR_UART,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (2.5, 0, 90, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                        LayoutTypeHierarchy.Level(
                            mod_type=B4B_ZR_SM4_TF,  # PM1006Connector,
                            layout=LayoutAbsolute(
                                F.has_pcb_position.Point(
                                    (13, 21, 180, F.has_pcb_position.layer_type.NONE)
                                )
                            ),
                        ),
                    ]
                )
            )
        )