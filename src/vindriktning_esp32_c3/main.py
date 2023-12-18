"""
TODO: Explain file
"""
import logging
import subprocess
import sys
from pathlib import Path

import typer
from faebryk.exporters.pcb.kicad.transformer import PCB_Transformer
from faebryk.exporters.visualize.graph import render_matrix
from faebryk.libs.app.kicad_netlist import write_netlist
from faebryk.libs.kicad.pcb import PCB
from faebryk.libs.logging import setup_basic_logging
from vindriktning_esp32_c3.app import SmartVindrikting
from vindriktning_esp32_c3.pcb import transform_pcb

# logging settings
logger = logging.getLogger(__name__)


def main(nonetlist: bool = False, nopcb: bool = False):
    # paths
    build_dir = Path("./build")
    faebryk_build_dir = build_dir.joinpath("faebryk")
    faebryk_build_dir.mkdir(parents=True, exist_ok=True)
    kicad_prj_path = Path(__file__).parent.parent.joinpath("kicad/main")
    netlist_path = kicad_prj_path.joinpath("main.net")
    pcbfile = kicad_prj_path.joinpath("main.kicad_pcb")

    def pcbnew():
        return subprocess.check_output(["pcbnew", pcbfile], stderr=subprocess.DEVNULL)

    # graph
    logger.info("Make app")
    try:
        sys.setrecursionlimit(10000)  # TODO needs optimization
        app = SmartVindrikting()
    except RecursionError:
        logger.error("RECURSION ERROR ABORTING")
        return

    logger.info("Build graph")
    G = app.get_graph()

    # visualize
    if True:
        render_matrix(
            G.G,
            nodes_rows=[],
            depth=1,
            show_full=True,
            show_non_sum=False,
        ).show()

    # netlist
    logger.info("Make netlist")
    netlist_updated = not nonetlist and write_netlist(
        G,
        netlist_path,
        use_kicad_designators=True,
    )

    # esphome
    logger.info("Make esphome config")
    # esphome_config = make_esphome_config(G)
    # for i2c_cfg in esphome_config["i2c"]:
    #    i2c_cfg["scan"] = True
    # faebryk_build_dir.joinpath("esphome.yaml").write_text(
    #    dump_esphome_config(esphome_config)
    # )

    if netlist_updated:
        logger.info("Opening kicad to import new netlist")
        print(
            f"Import the netlist at {netlist_path.as_posix()}. Press 'Update PCB'. "
            "Place the components, save the file and exit kicad."
        )
        # pcbnew()
        input()

    # pcb
    if nopcb:
        logger.info("Skipping PCB")
        return

    logger.info("Load PCB")
    pcb = PCB.load(pcbfile)

    transformer = PCB_Transformer(pcb, G, app.NODEs.mcu_pcb)

    logger.info("Transform PCB")
    transform_pcb(transformer)

    logger.info(f"Writing pcbfile {pcbfile}")
    pcb.dump(pcbfile)

    # pcbnew()


if __name__ == "__main__":
    setup_basic_logging()
    typer.run(main)
    # main()
