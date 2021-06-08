import Metashape
import os
import fileinput

import resources
# Python script for automated AGISOFT THERMAL processing

def make_rgb_mesh(rgb_img_folder, save_folder, opt_texture_size=4096, opt_mesh_quality = 'medium', opt_make_ortho = True):
    """
Function to create a mesh from rgb pictures, and export necessary files (e.g. camera positions)
    @param rgb_folder:
    @param save_folder:
    """
    # file names
    model_rgb_file = os.path.join(save_folder, 'mesh_rgb.obj')
    camera_ref_file = os.path.join(save_folder, 'cameras.txt')
    if opt_make_ortho:
        ortho_rgb_file = os.path.join(save_folder, 'ortho_rgb.tif')

    # new project
    doc = Metashape.Document()
    doc.save(path=save_folder + "/" + 'agisoft.psx')

    # creating new chunk for RGB
    chk = doc.addChunk()
    chk.label = 'RGB'

    # loading RGB images
    image_list = os.listdir(rgb_img_folder)
    photo_list = []
    for photo in image_list:
        photo_list.append("/".join([rgb_img_folder, photo]))
    chk.addPhotos(photo_list)

    chk.crs = Metashape.CoordinateSystem("EPSG::4326")
    chk.updateTransform()

    # proces RGB images
    chk.matchPhotos()
    chk.alignCameras()
    chk.buildDepthMaps()
    chk.buildModel(source_data=Metashape.DataSource.DepthMapsData)
    chk.buildUV(mapping_mode=Metashape.GenericMapping)
    chk.buildTexture(texture_size=opt_texture_size) # optional argument to change texture size
    Metashape.app.update()

    # export rgb model (mesh)
    chk.exportModel(path=model_rgb_file, precision=9, save_texture=True, save_uv=True, save_markers=False,
                      crs=Metashape.CoordinateSystem("EPSG::4326"))

    doc.save()
    # make ortho if needed
    if opt_make_ortho:
        chk.buildOrthomosaic(surface_data=Metashape.ModelData)
        chk.exportRaster(ortho_rgb_file)

    # export rgb camera orientations
    chk.exportReference(path=camera_ref_file, format=Metashape.ReferenceFormatCSV,
                          items=Metashape.ReferenceItemsCameras, columns='nuvwdefxyz', delimiter=' ')  # nox/y/zuvw

    # modify reference
    with fileinput.FileInput(camera_ref_file, inplace=True) as file:
        for line in file:
            print(line.replace('.jpg', '_thermal.png'), end='')


def make_thermal_mesh(rgb_model_folder, thermal_img_folder, save_folder, opt_use_masks = False,
                      opt_fixed_position = False, opt_make_ortho = True, opt_save_agisoft =  True):
    """
Function to import a rgb mesh file, and apply thermal texture
    @param rgb_model_folder:
    @param thermal_img_folder:
    @param save_folder:
    """
    # file names
    calib_file = resources.find('other/calib_V2.xml') # camera calibration file
    mask_file = resources.find('img/mask.png') # mask file
    model_rgb_file = os.path.join(rgb_model_folder, 'mesh_rgb.obj')
    model_th_file = os.path.join(save_folder, 'mesh_th.obj')

    doc = Metashape.Document()
    doc.save(path=save_folder + "/" + 'agisoft_thermal.psx')

    camera_ref_file = os.path.join(rgb_model_folder, 'cameras.txt') # camera loc and rot from rgb processing
    if opt_make_ortho:
        ortho_th_file = os.path.join(save_folder, 'ortho_th.tif')

    # creating new chunk for RGB en thermal
    chk = doc.addChunk()
    chk.label = 'thermal'

    T = chk.transform.matrix
    chk.crs = Metashape.CoordinateSystem("EPSG::4326")
    chk.updateTransform()

    # load thermal images in
    image_list = os.listdir(thermal_img_folder)
    photo_list = []
    for photo in image_list:
        photo_list.append("/".join([thermal_img_folder, photo]))
    chk.addPhotos(photo_list)

    # load masks if needed
    if opt_use_masks:
        chk.generateMasks(path=mask_file, masking_mode=Metashape.MaskingModeFile)

    # import calibration
    user_calib = Metashape.Calibration()
    user_calib.load(calib_file)

    # import RGB camera orientations for thermal images
    chk.importReference(path=camera_ref_file, format=Metashape.ReferenceFormatCSV, delimiter=' ', columns='nxyzabc',
                          skip_rows=2)

    # add calibration to cameras
    for camera in chk.cameras:
        camera.sensor.user_calib = user_calib
        camera.sensor.fixed = True
        camera.sensor.fixed_rotation = True

    # here distinction between fixed camera position, and method with camera alignment
    if not opt_fixed_position:
        chk.camera_location_accuracy = Metashape.Vector([0.02, 0.02, 0.02])
        chk.camera_rotation_accuracy = Metashape.Vector([0.5, 0.5, 0.5])
        chk.updateTransform()

        # proces thermal images
        chk.matchPhotos()
        chk.alignCameras()
    else:
        origin = None
        for camera in chk.cameras:
            if not camera.type == Metashape.Camera.Type.Regular:
                continue
            if not camera.reference.location:
                continue
            if not camera.reference.rotation:
                continue

            pos = crs.unproject(camera.reference.location)
            m = crs.localframe(pos)
            rot = Metashape.utils.ypr2mat(camera.reference.rotation) * Metashape.Matrix().Diag([1, -1, -1])
            R = Metashape.Matrix().Translation(pos) * Metashape.Matrix().Rotation(m.rotation().t() * rot)

            if not origin:
                origin = pos
                chk.transform.matrix = Metashape.Matrix().Translation(origin)
                T = chk.transform.matrix

            camera.transform = T.inv() * R
        chk.updateTransform()

    # last operations (importing model and creating texture)
    chk.importModel(path=model_rgb_file, format=Metashape.ModelFormatOBJ,
                          crs=Metashape.CoordinateSystem("EPSG::4326"))
    chk.buildTexture()
    chk.exportModel(path=model_th_file, precision=9, save_texture=True, save_uv=True, save_markers=False,
                      crs=Metashape.CoordinateSystem(
                          'LOCAL_CS["Local CS",LOCAL_DATUM["Local Datum",0],UNIT["metre",1]]'))

    # make ortho if needed
    doc.save()
    if opt_make_ortho:
        chk.buildOrthomosaic(surface_data=Metashape.ModelData, resolution=0.01)
        chk.exportRaster(ortho_th_file)

    if opt_save_agisoft:
        doc.save()



    
def create_ortho(agisoft_model_folder):
    doc = Metashape.Document()
    doc.open(path=agisoft_model_folder + "/" + 'agisoft.psx')
    for ch in doc.chunks:
        if ch.label == 'RGB':
            ch.buildOrthomosaic()
            ch.exportRaster(path=agisoft_model_folder + "/" + "orthomosaïc_RGB.tif")
        if ch.label == 'prethermal':
            ch.buildOrthomosaic()
            ch.exportRaster(path=agisoft_model_folder + "/" + "orthomosaïc_thermal_method1.tif")
        if ch.label == 'thermal':
            ch.buildOrthomosaic()
            ch.exportRaster(path=agisoft_model_folder + "/" + "orthomosaïc_thermal_method2.tif")

