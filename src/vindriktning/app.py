from faebryk.core.module import Module
from faebryk.libs.library import L
import faebryk.library._F as F
from faebryk.libs.units import P
from faebryk.libs.brightness import TypicalLuminousIntensity

from vindriktning.blocks.PCBMount import PCB_Mount
from vindriktning.blocks.VindriktningInterface import VindriktningInterface
from vindriktning.blocks.LEDString import LEDString
from vindriktning.blocks.MCU import MCU


class App(Module):
    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    vindriktning_interface: VindriktningInterface
    led_string = L.f_field(LEDString)(pixels=5, buffered=True)
    co2_sensor: F.SCD40
    mcu: MCU
    presence_sensor: F.HLK_LD2410B_P
    usb_psu: F.USB_C_PSU_Vertical
    lux_sensor: F.BH1750FVI_TR
    ldo_mcu: F.ME6211C33M5G_N
    ldo_peripheral: F.ME6211C33M5G_N
    pcb_mount: PCB_Mount
    qwiic_connector: F.QWIIC_Connector

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        # mcu has its own LDO
        self.ldo_mcu.power_out.connect(self.mcu.mcu.vdd3v3)
        # connect all 3.3V powers
        self.ldo_peripheral.power_out.connect(
            self.lux_sensor.ic.power,
            self.vindriktning_interface.power_data,
            self.co2_sensor.power,
            self.led_string.power_data,
        )

        # connect qwiic connector via fuse to 3.3V
        fused_power = self.qwiic_connector.power.fused(self.ldo_peripheral.power_out)
        fuse = fused_power.get_first_child_of_type(F.Fuse)
        fuse.trip_current.constrain_subset(
            L.Range.from_center_rel(550 * P.mA, 10 * P.percent)
        )
        fuse.fuse_type.alias_is(F.Fuse.FuseType.RESETTABLE)

        # connect all 5V powers
        self.usb_psu.power_out.connect(
            self.ldo_mcu.power_in,
            self.ldo_peripheral.power_in,
            self.presence_sensor.power,
            self.led_string.power,
            self.vindriktning_interface.power,
        )

        # pm sensor
        self.vindriktning_interface.uart.connect(
            self.mcu.mcu.esp32_c3_mini_1.ic.esp32_c3.uart[1]
        )
        # self.pm_sensor.uart.rx.connect(self.mcu.mcu.esp32_c3_mini_1.gpio[8])
        # self.pm_sensor.uart.tx.connect(self.mcu.mcu.esp32_c3_mini_1.gpio[9])
        self.vindriktning_interface.fan_enable.connect(
            self.mcu.mcu.esp32_c3_mini_1.ic.gpio[4]
        )

        # presence sensor
        self.presence_sensor.uart.connect(self.mcu.mcu.uart)
        self.presence_sensor.out.connect(self.mcu.mcu.esp32_c3_mini_1.ic.gpio[6])

        # I2C devices - connect individually
        i2c = self.mcu.mcu.esp32_c3_mini_1.ic.esp32_c3.i2c
        i2c.connect(self.co2_sensor.i2c, link=F.ElectricLogic.LinkIsolatedReference())
        i2c.connect(
            self.qwiic_connector.i2c, link=F.ElectricLogic.LinkIsolatedReference()
        )
        i2c.connect(
            self.lux_sensor.ic.i2c, link=F.ElectricLogic.LinkIsolatedReference()
        )

        # LEDs
        self.led_string.data_in.connect(
            self.mcu.mcu.esp32_c3_mini_1.ic.gpio[5],
            link=F.ElectricLogic.LinkIsolatedReference(),
        )

        # USB
        self.mcu.mcu.usb.connect(self.usb_psu.usb)

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        # esphome settings
        default_update_interval = 1 * P.s
        self.presence_sensor.esphome_config.throttle.constrain_subset(
            default_update_interval
        )
        self.lux_sensor.ic.esphome_config.update_interval.constrain_subset(
            default_update_interval
        )
        self.led_string.max_refresh_rate.constrain_subset(60 * P.Hz)
        self.co2_sensor.esphome_config.update_interval.constrain_subset(
            default_update_interval
        )

        for node in self.get_children(direct_only=False, types=F.PoweredLED):
            node.led.color.alias_is(F.LED.Color.RED)
            node.led.brightness.constrain_subset(
                TypicalLuminousIntensity.APPLICATION_LED_STANDBY.value
            )

        # TODO: fix decoupling cap values and sizes

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.vindriktning_interface.uart.connect(
            self.mcu.mcu.esp32_c3_mini_1.ic.esp32_c3.uart[1]
        )


class Vindriktning(Module):
    app: App
    pm1006: F.PM1006
    fan: F.Fan

    def __preinit__(self):
        self.app.vindriktning_interface.pm_sensor_connector.data.connect(
            self.pm1006.data
        )
        self.app.vindriktning_interface.pm_sensor_connector.power.connect(
            self.pm1006.power
        )
        self.app.vindriktning_interface.fan_controller.fan_connector.power.connect(
            self.fan.power
        )
        self.pm1006.esphome_config.update_interval.constrain_subset(20 * P.s)
