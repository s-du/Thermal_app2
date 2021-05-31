import Metashape
import os
import fileinput

import resources
# Python script for automated AGISOFT THERMAL processing

def make_thermal_mesh(low_res, main_folder, rgb_folder, thermal_folder, texture_size=4096, opt_mesh_quality = 'medium', opt_make_ortho = False):
    """

    :param low_res: whether to create a low_res mesh or not
    :param main_folder: folder for all agisoft files
    :param rgb_folder: folder with rgb images
    :param thermal_folder: folder with thermal images
    :return:
    """

    calib_file = resources.find('other/calib.xml')

    model_rgb_file = os.path.join(main_folder, 'mesh_rgb.obj')
    model_thermal_file_method1 = os.path.join(main_folder, 'mesh_thermal1.obj')
    model_thermal_file_method2 = os.path.join(main_folder, 'mesh_thermal2.obj')
    camera_ref_file = os.path.join(main_folder, 'cameras.txt')
    camera_ref_file2 = os.path.join(main_folder, 'cameras_th_estimated.txt')

    #new project
    doc = Metashape.Document()

    #creating new chunk for RGB en thermal
    chunkrgb = doc.addChunk()
    chunkrgb.label = 'RGB'

    chunkpreTHERMAL = doc.addChunk()
    chunkpreTHERMAL.label = 'prethermal'

    chunkTHERMAL = doc.addChunk()
    chunkTHERMAL.label = 'thermal'

    """
    ===========================================================
    RGB
    ==========================================================
    """
    chunk = chunkrgb

    # loading RGB images
    image_list = os.listdir(rgb_folder)
    photo_list = []
    for photo in image_list:
        photo_list.append("/".join([rgb_folder, photo]))
    chunk.addPhotos(photo_list)

    chunk.crs = Metashape.CoordinateSystem("EPSG::4326")
    chunk.updateTransform()

    #proces RGB images
    chunk.matchPhotos()
    chunk.alignCameras()
    chunk.buildDepthMaps()
    chunk.buildModel(source_data=Metashape.DataSource.DepthMapsData)
    chunk.buildUV(mapping_mode=Metashape.GenericMapping)
    chunk.buildTexture(texture_size=texture_size)
    Metashape.app.update()

    #export rgb model (mesh)
    chunk.exportModel(path=model_rgb_file, precision=9, save_texture=True, save_uv=True, save_markers=False, crs=Metashape.CoordinateSystem("EPSG::4326"))

    #export rgb camera orientations
    chunk.exportReference(path=camera_ref_file, format=Metashape.ReferenceFormatCSV, items=Metashape.ReferenceItemsCameras, columns='nuvwdefxyz', delimiter=' ') #nox/y/zuvw

    # modify reference
    with fileinput.FileInput(camera_ref_file, inplace=True) as file:
        for line in file:
            print(line.replace('.jpg', '_thermal.png'), end='')

    """
    ===========================================================
    PRE-THERMAL (with thermal image alignment)
    ==========================================================
    """
    chunk = chunkpreTHERMAL
    chunkpreTHERMAL.crs = Metashape.CoordinateSystem("EPSG::4326")
    chunkpreTHERMAL.updateTransform()

    # load thermal images in
    image_list = os.listdir(thermal_folder)
    photo_list = list()
    for photo in image_list:
        photo_list.append("/".join([thermal_folder, photo]))
    chunk.addPhotos(photo_list)

    # import calibration
    user_calib = Metashape.Calibration()
    user_calib.load(calib_file)

    # import RGB camera orientations for thermal images
    chunk.importReference(path=camera_ref_file, format=Metashape.ReferenceFormatCSV, delimiter=' ', columns='nxyzabc',
                          skip_rows=2)

    chunk.camera_location_accuracy = Metashape.Vector([0.02, 0.02, 0.02])
    chunk.camera_rotation_accuracy = Metashape.Vector([0.5, 0.5, 0.5])

    chunk.updateTransform()

    # add calibration to cameras
    for camera in chunk.cameras:
        camera.Reference.rotation_enabled = True
        camera.sensor.user_calib = user_calib
        camera.sensor.label = "mijnCamera"
        camera.sensor.fixed = True

    # proces thermal images
    chunk.matchPhotos()
    chunk.alignCameras()
    chunk.importModel(path=model_rgb_file, format=Metashape.ModelFormatOBJ,
                      crs=Metashape.CoordinateSystem("EPSG::4326"))  # p36

    chunk.buildTexture(texture_size=texture_size)
    chunk.exportModel(path=model_thermal_file_method1, precision=9, save_texture=True, save_uv=True, save_markers=False,
                      crs=Metashape.CoordinateSystem(
                          'LOCAL_CS["Local CS",LOCAL_DATUM["Local Datum",0],UNIT["metre",1]]'))

    # export rgb camera orientations
    chunk.exportReference(path=camera_ref_file2, format=Metashape.ReferenceFormatCSV,
                          items=Metashape.ReferenceItemsCameras, columns='nuvwdefxyz', delimiter=' ')  # nox/y/zuvw

    """
    ===========================================================
    THERMAL (thermal images only for texturing)
    ===========================================================
    """
    chunk = chunkTHERMAL
    crs = chunk.crs
    T = chunk.transform.matrix
    chunk.crs = Metashape.CoordinateSystem("EPSG::4326")
    chunk.updateTransform()

    #load thermal images in
    image_list = os.listdir(thermal_folder)
    photo_list = list()
    for photo in image_list:
        photo_list.append("/".join([thermal_folder, photo]))
    chunk.addPhotos(photo_list)

    #import calibration
    user_calib = Metashape.Calibration()
    user_calib.load(calib_file)

    # import RGB camera orientations for thermal images
    chunk.importReference(path=camera_ref_file, format=Metashape.ReferenceFormatCSV, delimiter=' ', columns='nxyzabc',
                          skip_rows=2)

    #add calibration to cameras
    for camera in chunk.cameras:
        camera.sensor.user_calib = user_calib
        camera.sensor.label = "mijnCamera"
        camera.sensor.fixed = True

    # From forum
    origin = None
    for camera in chunk.cameras:
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
            chunk.transform.matrix = Metashape.Matrix().Translation(origin)
            T = chunk.transform.matrix

        camera.transform = T.inv() * R
    chunk.updateTransform()

    #import rgbmesh
    chunk.importModel(path=model_rgb_file, format=Metashape.ModelFormatOBJ, crs=Metashape.CoordinateSystem("EPSG::4326")) #p36

    chunk.buildTexture(texture_size=texture_size)
    chunk.exportModel(path=model_thermal_file_method2, precision=9, save_texture=True, save_uv=True, save_markers=False, crs=Metashape.CoordinateSystem('LOCAL_CS["Local CS",LOCAL_DATUM["Local Datum",0],UNIT["metre",1]]'))

    doc.save(path=main_folder + "/" + 'agisoft.psx', chunks=[chunkrgb, chunkpreTHERMAL, chunkTHERMAL])

    os.remove(camera_ref_file)

