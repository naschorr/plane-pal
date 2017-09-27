import os
import time
import math
from PIL import Image, ImageDraw

import utilities


## Config
CONFIG_OPTIONS = utilities.load_config()


## Todo: genericize and move into bot_io.py?
class PlotterFileController:
    ## Keys
    RESOURCES_FOLDER_KEY = "resources_folder"
    RESOURCES_FOLDER_PATH_KEY = "resources_folder_path"
    MAP_FILE_KEY = "map_file"
    MAP_FILE_PATH_KEY = "map_file_path"
    MAP_FILE_EXTENSION_KEY = "map_file_extension"
    OUTPUT_FOLDER_KEY = "output_folder"
    OUTPUT_FOLDER_PATH_KEY = "output_folder_path"

    ## Defaults
    RESOURCES_FOLDER = CONFIG_OPTIONS.get(RESOURCES_FOLDER_KEY, "resources")
    RESOURCES_FOLDER_PATH = CONFIG_OPTIONS.get(RESOURCES_FOLDER_PATH_KEY, os.sep.join([utilities.get_root_path(), RESOURCES_FOLDER]))
    MAP_FILE = CONFIG_OPTIONS.get(MAP_FILE_KEY, "map.jpg")
    MAP_FILE_PATH = CONFIG_OPTIONS.get(MAP_FILE_PATH_KEY, os.sep.join([RESOURCES_FOLDER_PATH, MAP_FILE]))
    MAP_FILE_EXTENSION = CONFIG_OPTIONS.get(MAP_FILE_EXTENSION_KEY, "jpeg")
    OUTPUT_FOLDER = CONFIG_OPTIONS.get(OUTPUT_FOLDER_KEY, "temp")
    OUTPUT_FOLDER_PATH = CONFIG_OPTIONS.get(OUTPUT_FOLDER_PATH_KEY, os.sep.join([utilities.get_root_path(), OUTPUT_FOLDER]))


    def __init__(self, **kwargs):
        self.map_file_path = kwargs.get(self.MAP_FILE_PATH_KEY, self.MAP_FILE_PATH)
        self.map_file_extension = kwargs.get(self.MAP_FILE_EXTENSION_KEY, self.MAP_FILE_EXTENSION)
        self.output_folder_path = kwargs.get(self.OUTPUT_FOLDER_PATH_KEY, self.OUTPUT_FOLDER_PATH)

        ## Prep the temp dir for image saving/deletion
        if(self.output_folder_path):
            self._init_dir()


    def _init_dir(self):
        if(not os.path.exists(self.output_folder_path)):
            os.makedirs(self.output_folder_path)
        else:
            for root, dirs, files in os.walk(self.output_folder_path, topdown=False):
                for file in files:
                    try:
                        os.remove(os.sep.join([root, file]))
                    except OSError as e:
                        utilities.debug_print("Error removing file: {}, during temp dir cleanup.".format(file), e, debug_level=2)


    def _generate_unique_file_name(self, extension):
        time_ms = int(time.time() * 1000)
        file_name = "{}.{}".format(time_ms, extension)

        while(os.path.isfile(file_name)):
            time_ms -= 1
            file_name = "{}.{}".format(time_ms, extension)

        return file_name


    def load_base_map(self):
        try:
            return Image.open(self.map_file_path)
        except Exception as e:
            utilities.debug_print("Error opening base_map.", e, debug_level=0)
            return None


    def save_map(self, pillow_image):
        file_name = self._generate_unique_file_name(self.map_file_extension)
        file_path = os.sep.join([self.output_folder_path, file_name])
        try:
            pillow_image.save(file_path, format=self.map_file_extension)
        except IOError as e:
            utilities.debug_print("Unable to save image at: '{}'.".format(file_path), e, debug_level=0)
            return None
        else:
            return file_path


    def create_delete_map_callback(self, path):
        def _delete_map_callback():
            try:
                os.remove(path)
            except OSError as e:
                utilities.debug_print("Error deleting map at: '{}'.".format(path), e, debug_level=1)
                return False

            return True
        
        return _delete_map_callback


class Plotter:
    ## Keys
    PLANE_PATH_WIDTH_KM_KEY = "plane_path_width_km"
    PLANE_PATH_COLOR_KEY = "plane_path_color"
    FAST_PARACHUTE_PATH_WIDTH_KM_KEY = "fast_parachute_path_width_km"
    FAST_PARACHUTE_PATH_COLOR_KEY = "fast_parachute_path_color"
    SLOW_PARACHUTE_PATH_WIDTH_KM_KEY = "slow_parachute_path_width_km"
    SLOW_PARACHUTE_PATH_COLOR_KEY = "slow_parachute_path_color"

    ## Defaults
    PLANE_PATH_WIDTH_KM = CONFIG_OPTIONS.get(PLANE_PATH_WIDTH_KM_KEY, 0.1)
    PLANE_PATH_COLOR = CONFIG_OPTIONS.get(PLANE_PATH_COLOR_KEY, "white")
    FAST_PARACHUTE_PATH_WIDTH_KM = CONFIG_OPTIONS.get(FAST_PARACHUTE_PATH_WIDTH_KM_KEY, 1.4)
    FAST_PARACHUTE_PATH_COLOR = CONFIG_OPTIONS.get(FAST_PARACHUTE_PATH_COLOR_KEY, "red")
    SLOW_PARACHUTE_PATH_WIDTH_KM = CONFIG_OPTIONS.get(SLOW_PARACHUTE_PATH_WIDTH_KM_KEY, 3)
    SLOW_PARACHUTE_PATH_COLOR = CONFIG_OPTIONS.get(SLOW_PARACHUTE_PATH_COLOR_KEY, "orange")


    def __init__(self, **kwargs):
        self.file_controller = PlotterFileController(**kwargs)
        self.base_map = self.file_controller.load_base_map()

        self.pixels_per_km = self.base_map.size[0] // 8

        self.plane_path_width_km = float(kwargs.get(self.PLANE_PATH_WIDTH_KM_KEY, self.PLANE_PATH_WIDTH_KM))
        self.plane_path_color = kwargs.get(self.PLANE_PATH_COLOR_KEY, self.PLANE_PATH_COLOR)
        self.fast_parachute_path_width_km = float(kwargs.get(self.FAST_PARACHUTE_PATH_WIDTH_KM_KEY, self.FAST_PARACHUTE_PATH_WIDTH_KM))
        self.fast_parachute_path_color = kwargs.get(self.FAST_PARACHUTE_PATH_COLOR_KEY, self.FAST_PARACHUTE_PATH_COLOR)
        self.slow_parachute_path_width_km = float(kwargs.get(self.SLOW_PARACHUTE_PATH_WIDTH_KM_KEY, self.SLOW_PARACHUTE_PATH_WIDTH_KM))
        self.slow_parachute_path_color = kwargs.get(self.SLOW_PARACHUTE_PATH_COLOR_KEY, self.SLOW_PARACHUTE_PATH_COLOR)


    def _plot_line(self, image, x1, y1, x2, y2, width, color):
        draw = ImageDraw.Draw(image, "RGBA")
        draw.line([x1, y1, x2, y2], fill=color, width=width)
        del draw

        return image


    def plot_plane_path(self, path_obj):
        ## Get a copy of the map, so it's never overridden
        base_map = self.base_map.copy()

        ## Get the height and width of the map image, and calculate the diagonal's length
        map_width, map_height = base_map.size
        map_diagonal_length = int(math.sqrt(pow(map_width, 2) + pow(map_height, 2)))

        ## Get the x, y, and angle supplied by the user
        x = path_obj.grid_obj.get_true_x(self.pixels_per_km)
        y = path_obj.grid_obj.get_true_y(self.pixels_per_km)
        angle = math.radians(path_obj.heading_obj.angle)

        ## Generate the x and y coord pairs for the plane's path line
        x1 = x - map_diagonal_length * math.cos(angle)
        y1 = y + map_diagonal_length * math.sin(angle)  ## Invert both the y components; upside down coordinate system
        x2 = x + map_diagonal_length * math.cos(angle)
        y2 = y - map_diagonal_length * math.sin(angle)

        ## Prep line widths
        plane_path_width = int(self.plane_path_width_km * self.pixels_per_km)
        ## *2 because the width is only half of what it should be, since players can drop in any direction
        fast_parachute_path_width = int(self.fast_parachute_path_width_km * self.pixels_per_km * 2)
        slow_parachute_path_width = int(self.slow_parachute_path_width_km * self.pixels_per_km * 2)

        ## Plot the requisite lines
        ## Todo: plot in place?
        plotted_map = self._plot_line(base_map, x1, y1, x2, y2, slow_parachute_path_width, self.slow_parachute_path_color)
        plotted_map = self._plot_line(base_map, x1, y1, x2, y2, fast_parachute_path_width, self.fast_parachute_path_color)
        plotted_map = self._plot_line(base_map, x1, y1, x2, y2, plane_path_width, self.plane_path_color)

        ## Save and return the final map
        return self.file_controller.save_map(plotted_map)