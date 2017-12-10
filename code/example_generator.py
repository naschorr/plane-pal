import os
from PIL import Image, ImageDraw

import utilities
import plotter
import bot_io

## Config
CONFIG_OPTIONS = utilities.load_config()

EXAMPLE_SIZE = (540, 540)
EXAMPLE_RESIZE_FILTER = Image.LANCZOS
EXAMPLES = [
    ["erangel", "ak1 90"],
    ["erangel", "al7 105"],
    ["erangel", "ep 355"],
    ["erangel", "gp7 330"],
    ["erangel", "hn 275"],
    ["miramar", "al 115"],
    ["miramar", "ei1 175"],
    ["miramar", "ho 280"]
]

class ExampleGenerator:
    def __init__(self):
        self.path_parser = bot_io.PathParser()
        # Passes kwargs onto PlotterFileController
        self.plotter = plotter.Plotter(output_folder_path=os.sep.join([utilities.get_root_path(), "resources", "examples"]))
        self.plotter.file_controller._init_dir()    # Clean up the examples dir

        for map_name, message in EXAMPLES:
            path_obj = self.path_parser.parse_message(message)
            plotted_map = self.plotter.plot_plane_path(map_name, path_obj)
            plotted_map = plotted_map.resize(EXAMPLE_SIZE, EXAMPLE_RESIZE_FILTER)
            self.plotter.file_controller.save_map(plotted_map, "{} {}.{}".format(map_name, message, self.plotter.file_controller.map_file_extension))


if(__name__ == '__main__'):
    ExampleGenerator()
