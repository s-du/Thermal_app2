import os
from shutil import copyfile, copytree
from tools import flir_image_extractor
import numpy as np
fir = flir_image_extractor.FlirImageExtractor()


def rename_from_exif(img_folder):
    pass

def sort_image_method1(img_folder, rgb_folder, th_folder, string_to_search):
    """
    this function is adapted to sort all images from a folder, where those images are a mix between thermal and corresponding rgb
    """
    # Sorting images in new folders

    rgb_count = 1
    th_count = 1
    for file in os.listdir(img_folder):

        if file.endswith('.jpg') or file.endswith('.JPG'):
            if string_to_search in str(file):
                new_file = 'image_' + str(th_count) + '.jpg'
                copyfile(os.path.join(img_folder, file), os.path.join(th_folder, new_file))
                th_count += 1
            else:
                new_file = 'image_' + str(rgb_count) + '.jpg'
                copyfile(os.path.join(img_folder, file), os.path.join(rgb_folder, new_file))
                rgb_count += 1


def process_all_th_pictures(origin_folder, dest_folder, tmin, tmax, colormap, mode, meta = 'fixed'):
    """
    this function process all thermal pictures in a folder
    """
    list_img = os.listdir(origin_folder)
    # get metadata (reflectivity, temp, etc.) from first thermal picture
    first_meta = list_img[0]
    ref_path = os.path.join(origin_folder, first_meta)


    for file in os.listdir(origin_folder):
        if file.endswith('.jpg'):
            copyfile(os.path.join(origin_folder, file), os.path.join(dest_folder, file))
            file_path = os.path.join(dest_folder, file)

            if meta != 'fixed':
                fir.process_image(file_path, file_path)
            else:
                fir.process_image(file_path, ref_path)
            fir.save_images(tmin, tmax, colormap, mode)
            os.remove(file_path)

def compute_delta(img_path):
    fir.process_image(img_path, img_path)
    thermal_np = fir.thermal_image_np
    comp_tmin = np.amin(thermal_np)
    comp_tmax = np.amax(thermal_np)

    return comp_tmin, comp_tmax