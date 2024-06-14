"""
TODO: Explain file
"""

import logging
import sys
from pathlib import Path

import faebryk.libs.picker.lcsc as lcsc
import typer
from faebryk.core.util import get_all_modules
from faebryk.exporters.bom.jlcpcb import write_bom_jlcpcb
from faebryk.exporters.esphome.esphome import make_esphome_config
from faebryk.exporters.pcb.kicad.transformer import PCB_Transformer
from faebryk.exporters.visualize.graph import render_matrix
from faebryk.libs.app.erc import simple_erc
from faebryk.libs.app.kicad_netlist import write_netlist
from faebryk.libs.app.parameters import replace_tbd_with_any
from faebryk.libs.kicad.pcb import PCB
from faebryk.libs.logging import setup_basic_logging
from faebryk.libs.picker.picker import pick_part_recursively
from vindriktning_esp32_c3.app import SmartVindrikting
from vindriktning_esp32_c3.pcb import transform_pcb
from vindriktning_esp32_c3.pickers import pick

# logging settings
logger = logging.getLogger(__name__)


def main(
    nonetlist: bool = False,
    nopcb: bool = False,
    nobom: bool = False,
    visualize: bool = False,
):
    # paths --------------------------------------------------
    build_dir = Path("./build")
    faebryk_build_dir = build_dir.joinpath("faebryk")
    faebryk_build_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).parent.parent.parent
    netlist_path = faebryk_build_dir.joinpath("faebryk.net")
    kicad_prj_path = root.joinpath("source")
    pcbfile = kicad_prj_path.joinpath("main.kicad_pcb")
    bom_dir = build_dir
    bom_path = bom_dir.joinpath("bom.csv")
    esphome_path = build_dir.joinpath("esphome")
    esphome_config_path = esphome_path.joinpath("esphome.yaml")

    lcsc.BUILD_FOLDER = build_dir
    lcsc.LIB_FOLDER = root.joinpath("libs")

    # graph --------------------------------------------------
    logger.info("Make app")
    try:
        sys.setrecursionlimit(20000)  # TODO needs optimization
        app = SmartVindrikting()
    except RecursionError:
        logger.error("RECURSION ERROR ABORTING")
        return
    logger.info("Build graph")
    G = app.get_graph()

    # visualize ----------------------------------------------
    if visualize:
        logger.info("Visualize graph")
        render_matrix(
            G.G,
            nodes_rows=[],
            depth=1,
            show_full=True,
            show_non_sum=False,
        ).show()

    # fill unspecified parameters ----------------------------
    logger.info("Filling unspecified parameters")
    import faebryk.libs.app.parameters as p_mod

    lvl = p_mod.logger.getEffectiveLevel()
    p_mod.logger.setLevel(logging.DEBUG)
    replace_tbd_with_any(app, recursive=True)
    p_mod.logger.setLevel(lvl)

    # pick parts ---------------------------------------------
    logger.info("Picking parts")
    pick_part_recursively(app, pick)
    G = app.get_graph()
    simple_erc(G)

    # netlist -----------------------------------------------
    if not nonetlist:
        logger.info(f"Writing netlist to {netlist_path}")
        write_netlist(G, netlist_path, use_kicad_designators=True)

    # pcb ----------------------------------------------------
    if not nopcb:
        logger.info("Load PCB")
        pcb = PCB.load(pcbfile)

        transformer = PCB_Transformer(pcb, G, app)

        logger.info("Transform PCB")
        transform_pcb(transformer)

        logger.info(f"Writing pcbfile {pcbfile}")
        pcb.dump(pcbfile)
    # ---------------------------------------------------------

    # bom ----------------------------------------------------
    if not nobom:
        logger.info("Generating BOM")
        write_bom_jlcpcb(get_all_modules(app), bom_path)

    # esphome config -----------------------------------------
    logger.info("Generating esphome config")
    esphome_config = make_esphome_config(G)
    esphome_config_path.write_text(esphome_config, encoding="utf-8")


if __name__ == "__main__":
    setup_basic_logging()
    typer.run(main)
