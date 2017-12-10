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
    MAP_FILES_KEY = "map_files"
    MAP_FILE_PATHS_KEY = "map_file_paths"
    MAP_FILE_EXTENSION_KEY = "map_file_extension"
    OUTPUT_FOLDER_KEY = "output_folder"
    OUTPUT_FOLDER_PATH_KEY = "output_folder_path"

    ## Defaults
    RESOURCES_FOLDER = CONFIG_OPTIONS.get(RESOURCES_FOLDER_KEY, "resources")
    RESOURCES_FOLDER_PATH = CONFIG_OPTIONS.get(RESOURCES_FOLDER_PATH_KEY, os.sep.join([utilities.get_root_path(), RESOURCES_FOLDER]))
    MAP_FILES = CONFIG_OPTIONS.get(MAP_FILES_KEY, {})
    MAP_FILE_PATHS = CONFIG_OPTIONS.get(MAP_FILE_PATHS_KEY, {})
    MAP_FILE_EXTENSION = CONFIG_OPTIONS.get(MAP_FILE_EXTENSION_KEY, "jpeg")
    OUTPUT_FOLDER = CONFIG_OPTIONS.get(OUTPUT_FOLDER_KEY, "temp")
    OUTPUT_FOLDER_PATH = CONFIG_OPTIONS.get(OUTPUT_FOLDER_PATH_KEY, os.sep.join([utilities.get_root_path(), OUTPUT_FOLDER]))


    def __init__(self, **kwargs):
        self.map_file_paths = kwargs.get(self.MAP_FILE_PATHS_KEY)
        if(not self.MAP_FILE_PATHS):
            self.map_file_paths = {}
            for map_name, map_path in self.MAP_FILES.items():
                self.map_file_paths[map_name] = os.sep.join([self.RESOURCES_FOLDER_PATH, map_path])

        self.map_file_extension = kwargs.get(self.MAP_FILE_EXTENSION_KEY, self.MAP_FILE_EXTENSION)
        self.output_folder_path = kwargs.get(self.OUTPUT_FOLDER_PATH_KEY, self.OUTPUT_FOLDER_PATH)

        self.maps = {}

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


    def load_base_maps(self):
        maps = {}
        try:
            for map_name, map_path in self.map_file_paths.items():
                maps[map_name] = Image.open(map_path)
        except Exception as e:
            utilities.debug_print("Error opening base_map.", e, debug_level=0)
        
        return maps


    def save_map(self, pillow_image, file_name=None):
        file_name = self._generate_unique_file_name(self.map_file_extension) if not file_name else file_name
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
    SHORT_PARACHUTE_PATH_WIDTH_KM_KEY = "short_parachute_path_width_km"
    SHORT_PARACHUTE_PATH_COLOR_KEY = "short_parachute_path_color"
    LONG_PARACHUTE_PATH_WIDTH_KM_KEY = "long_parachute_path_width_km"
    LONG_PARACHUTE_PATH_COLOR_KEY = "long_parachute_path_color"
    TRIANGLE_SIZE_KM_KEY = "triangle_size_km"
    TRIANGLE_COLOR_KEY = "triangle_color"

    ## Defaults
    PLANE_PATH_WIDTH_KM = CONFIG_OPTIONS.get(PLANE_PATH_WIDTH_KM_KEY, 0.1)
    PLANE_PATH_COLOR = CONFIG_OPTIONS.get(PLANE_PATH_COLOR_KEY, "white")
    SHORT_PARACHUTE_PATH_WIDTH_KM = CONFIG_OPTIONS.get(SHORT_PARACHUTE_PATH_WIDTH_KM_KEY, 1.4)
    SHORT_PARACHUTE_PATH_COLOR = CONFIG_OPTIONS.get(SHORT_PARACHUTE_PATH_COLOR_KEY, "red")
    LONG_PARACHUTE_PATH_WIDTH_KM = CONFIG_OPTIONS.get(LONG_PARACHUTE_PATH_WIDTH_KM_KEY, 3)
    LONG_PARACHUTE_PATH_COLOR = CONFIG_OPTIONS.get(LONG_PARACHUTE_PATH_COLOR_KEY, "orange")
    TRIANGLE_SIZE_KM = CONFIG_OPTIONS.get(TRIANGLE_SIZE_KM_KEY, 0.2)
    TRIANGLE_COLOR = CONFIG_OPTIONS.get(TRIANGLE_COLOR_KEY, "white")


    def __init__(self, **kwargs):
        self.file_controller = PlotterFileController(**kwargs)
        self.base_maps = self.file_controller.load_base_maps()

        self.plane_path_width_km = float(kwargs.get(self.PLANE_PATH_WIDTH_KM_KEY, self.PLANE_PATH_WIDTH_KM))
        self.plane_path_color = kwargs.get(self.PLANE_PATH_COLOR_KEY, self.PLANE_PATH_COLOR)
        self.short_parachute_path_width_km = float(kwargs.get(self.SHORT_PARACHUTE_PATH_WIDTH_KM_KEY, self.SHORT_PARACHUTE_PATH_WIDTH_KM))
        self.short_parachute_path_color = kwargs.get(self.SHORT_PARACHUTE_PATH_COLOR_KEY, self.SHORT_PARACHUTE_PATH_COLOR)
        self.long_parachute_path_width_km = float(kwargs.get(self.LONG_PARACHUTE_PATH_WIDTH_KM_KEY, self.LONG_PARACHUTE_PATH_WIDTH_KM))
        self.long_parachute_path_color = kwargs.get(self.LONG_PARACHUTE_PATH_COLOR_KEY, self.LONG_PARACHUTE_PATH_COLOR)
        self.triangle_size_km = kwargs.get(self.TRIANGLE_SIZE_KM_KEY, self.TRIANGLE_SIZE_KM)
        self.triangle_color = kwargs.get(self.TRIANGLE_COLOR_KEY, self.TRIANGLE_COLOR)


    def _rotate_coordinate(self, x, y, angle):
        """
        Rotate a given coordinate around the origin by the specified angle.
        """

        sin = math.sin(angle)
        cos = math.cos(angle)

        x_ = x * cos - y * sin
        y_ = x * sin + y * cos

        return (x_, y_)


    def _scale_coordinate(self, x, y, scale_factor):
        """
        Scale a given point by the given scale factor from the origin.
        """

        return (x * scale_factor, y * scale_factor)

    
    def _translate_coordinate(self, x1, y1, x2, y2):
        """
        Translate a given point relative another point.
        """

        return (x1 + x2, y1 + y2)


    def _plot_line(self, image, x1, y1, x2, y2, width, color):
        """
        Plot a line from (x1,y1) to (x2,y2) with a thickness of 'width' and colored in with 'color'.
        """

        draw = ImageDraw.Draw(image, "RGBA")
        draw.line([x1, y1, x2, y2], fill=color, width=width)
        del draw

        return image


    def _plot_triangle(self, image, x, y, rotation, side_length, color):
        """
        Plot a triangle centered on (x,y), rotated 'rotation' degrees clockwise from the east, and has side lengths of 
        'side_length' and colored in with 'color'.
        """

        ## Precalculate the 'unit' triangle's centered coords, facing east
        coords = [(-0.283, -0.5), (-0.283, 0.5), (0.567, 0)]
        ## Calculate the triangle's side length scaling factor
        scale_factor = side_length / 1

        ## Scale, rotate, and translate the coords about the origin
        for index, coord in enumerate(coords):
            _x, _y = self._rotate_coordinate(*coord, -rotation)
            _x, _y = self._scale_coordinate(_x, _y, scale_factor)
            coords[index] = self._translate_coordinate(_x, _y, x, y)

        draw = ImageDraw.Draw(image, "RGBA")
        draw.polygon(coords, fill=color, outline=color)
        del draw

        return image


    def plot_plane_path(self, map_name, path_obj):
        ## Get a copy of the map, so it's never overridden
        base_map = self.base_maps[map_name].copy()
        pixels_per_km = base_map.size[0] // 8

        ## Get the height and width of the map image, and calculate the diagonal's length
        map_width, map_height = base_map.size
        map_diagonal_length = int(math.sqrt(pow(map_width, 2) + pow(map_height, 2)))

        ## Get the x, y, and angle supplied by the user
        x = path_obj.grid_obj.get_true_x(pixels_per_km)
        y = path_obj.grid_obj.get_true_y(pixels_per_km)
        angle = math.radians(path_obj.heading_obj.angle)

        ## Generate the x and y coord pairs for the plane's path line
        x1 = x - map_diagonal_length * math.cos(angle)
        y1 = y + map_diagonal_length * math.sin(angle)  ## Invert both the y components; upside down coordinate system
        x2 = x + map_diagonal_length * math.cos(angle)
        y2 = y - map_diagonal_length * math.sin(angle)

        ## Prep widths
        plane_path_width = int(self.plane_path_width_km * pixels_per_km)
        triangle_size = int(self.triangle_size_km * pixels_per_km)
        ## *2 because the width is only half of what it should be, since players can drop in any direction
        short_parachute_path_width = int(self.short_parachute_path_width_km * pixels_per_km * 2)
        long_parachute_path_width = int(self.long_parachute_path_width_km * pixels_per_km * 2)

        ## Plot the requisite lines
        ## Todo: plot in place?
        plotted_map = self._plot_line(base_map, x1, y1, x2, y2, long_parachute_path_width, self.long_parachute_path_color)
        plotted_map = self._plot_line(base_map, x1, y1, x2, y2, short_parachute_path_width, self.short_parachute_path_color)
        plotted_map = self._plot_line(base_map, x1, y1, x2, y2, plane_path_width, self.plane_path_color)
        plotted_map = self._plot_triangle(base_map, x, y, angle, triangle_size, self.triangle_color)

        ## return the final map
        return plotted_map
