""" MAIN POINTIFY APP : Defining user interaction """

import os.path
from shutil import copyfile, copytree
import fileinput
import threading
import http.server
import socketserver
import open3d as o3d

# import Pyqt packages
import PyQt5.uic
from PyQt5 import QtCore, QtGui, QtWidgets
from qt_material import apply_stylesheet

# import custom packages
import resources
from tools import thermal_tools as tt
from tools import agisoft_part

class dialog_mesh_preview(QtWidgets.QDialog):
    """
    Dialog that opens finding specific walls
    """
    def __init__(self, parent=None):

        QtWidgets.QDialog.__init__(self)
        basepath = os.path.dirname(__file__)
        basename = 'meshpreview'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)

        # modify html

        # button actions
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


    def set_folder_to_stream(self, folder):
        def http_launch(path):
            """
            A function to launch a http server active on the installation directory
            :param path:
            :return:
            """
            os.chdir(path)
            PORT = 8080
            Handler = http.server.SimpleHTTPRequestHandler

            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print("serving at port", PORT)
                httpd.serve_forever()

        # Launch http server
        x = threading.Thread(target=http_launch, args=(folder,), daemon=True)
        x.start()

        # open 3D view
        threejs_url = 'http://localhost:8080/threejs/page/index.html'
        self.webEngineView_threejs.setUrl(QtCore.QUrl(threejs_url))


class dialog_prepare_images(QtWidgets.QDialog):
    """
    Dialog that opens finding specific walls
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        basepath = os.path.dirname(__file__)
        basename = 'preparepictures'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)

        # initialize variables
        self.img_folder = ''

        # Initialize combobox
        # Fill combobox with colormaps choices
        self.colormap_list = ['plasma', 'inferno', 'Greys', 'Greys_r', 'coolwarm', 'jet', 'rainbow', 'Spectral']
        self.comboBox.addItems(self.colormap_list)

        to_find = 'img/plasma.png'
        pixmap = QtGui.QPixmap(resources.find(to_find))
        pixmap = pixmap.scaledToWidth(200)
        self.label_thumb.setPixmap(pixmap)
        self.label_thumb.show()

        # connections
        self.create_connections()

    def create_connections(self):
        self.pushButton_estimate.clicked.connect(self.go_estimate)
        self.comboBox.currentIndexChanged.connect(self.on_combo_changed)

        # button actions
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def go_estimate(self):
        # Note: to add: error if not a thermal file
        ref_pic_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',
                                            'c:\\', "Image files (*.jpg *.gif)")
        img_path = ref_pic_name[0]
        if img_path != '':
            tmin, tmax = tt.compute_delta(img_path)

            self.lineEdit_min_temp.setText(str(round(tmin, 2)))
            self.lineEdit_max_temp.setText(str(round(tmax, 2)))

    def on_combo_changed(self):
        i = self.comboBox.currentIndex()
        img_thumb_list = ['plasma.png', 'inferno.png', 'greys.png', 'greys_r.png', 'coolwarm.png', 'jet.png', 'rainbow.png', 'spectral_r.png']
        to_find = 'img/' + img_thumb_list[i]
        pixmap = QtGui.QPixmap(resources.find(to_find))
        pixmap = pixmap.scaledToWidth(200)
        self.label_thumb.setPixmap(pixmap)
        self.label_thumb.show()


class dialog_make_model(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        basepath = os.path.dirname(__file__)
        basename = 'makemodel'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)

        self.th_datasets_list = []

        self.quality_list = ['low', 'medium', 'high', 'veryhigh']
        self.comboBox_quality.addItems(self.quality_list)

        self.texture_list = ['1024', '2048', '4096', '8192']
        self.comboBox_texture.addItems(self.texture_list)

        # button actions
        self.checkBox_model.stateChanged.connect(self.disable)
        self.buttonBox.accepted.connect(self.return_values)
        self.buttonBox.rejected.connect(self.reject)
    def disable(self):
        if self.comboBox_texture.isEnabled():
            self.comboBox_texture.setEnabled(False)
            self.comboBox_quality.setEnabled(False)
        else:
            self.comboBox_texture.setEnabled(True)
            self.comboBox_quality.setEnabled(True)

    def fill_comb(self):
        # fill comboboxes
        self.comboBox_thimg.addItems(self.th_datasets_list)

    def return_values(self):
        self.do_rec = self.checkBox_model.isChecked()
        self.masked = self.checkBox_masks.isChecked()
        self.ortho = self.checkBox_ortho.isChecked()
        self.img_set_index = self.comboBox_thimg.currentIndex()
        self.texture = self.texture_list[self.comboBox_texture.currentIndex()]
        self.quality = self.quality_list[self.comboBox_quality.currentIndex()]

class ThermalWindow(QtWidgets.QMainWindow):
    """
    Main Window class for the Pointify application.
    """

    def __init__(self, parent=None):
        """
        Function to initialize the class
        :param parent:
        """
        super(ThermalWindow, self).__init__(parent)

        # load the ui
        basepath = os.path.dirname(__file__)
        basename = 'thermalmesh'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)

        # create empty list of processes
        self.proc_list = [] # list of processed thermal image sets
        self.thermal_process_img_folders = [] # list of folders containing thermal image sets
        self.th_mesh_folders = [] # list of folders containing thermal meshes
        self.rgb_mesh_done = False

        # define useful paths
        self.gui_folder = os.path.dirname(__file__)

        # initialize status
        self.update_progress("Status: Choose images or project!", 0)

        # create connections (signals)
        self.create_connections()

    def create_connections(self):
        # 'Simplify buttons'
        self.pushButton_load_img.clicked.connect(self.load_img)
        self.pushButton_load_project.clicked.connect(self.load_project)
        self.pushButton_go_img.clicked.connect(self.go_img)
        self.pushButton_go_mesh.clicked.connect(self.go_mesh)
        self.pushButton_go_visu.clicked.connect(self.go_visu)

    def update_progress(self, text, nb):
        self.label_status.setText(text)
        self.progressBar.setProperty("value", nb)

    def load_img(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

        # sort images
        if not folder == "": # if user cancel selection, stop function
            self.main_folder = folder
            self.app_folder = os.path.join(folder, 'thermalMesh')

            text, ok = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog', 'Enter the specific string in thermal image:')

            if ok:
                # create a subfolder for thermal images, that incorporates the propoerties of the processing
                self.original_th_img_folder = os.path.join(self.app_folder, 'img_th_original')
                self.rgb_img_folder = os.path.join(self.app_folder, 'img_rgb')

                # if the subfolder do not exist, create them
                if not os.path.exists(self.app_folder):
                    os.mkdir(self.app_folder)
                if not os.path.exists(self.original_th_img_folder):
                    os.mkdir(self.original_th_img_folder)
                if not os.path.exists(self.rgb_img_folder):
                    os.mkdir(self.rgb_img_folder)

                tt.sort_image_method1(self.main_folder, self.rgb_img_folder, self.original_th_img_folder, text)

            # enable actions for user
            self.pushButton_go_img.setEnabled(True)

            # update status
            self.update_progress("Status: You can now process thermal images!", 0)

    def load_project(self):
        self.app_folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.original_th_img_folder = os.path.join(self.app_folder, 'img_th_original')
        self.rgb_img_folder = os.path.join(self.app_folder, 'img_rgb')

        # check existing folder with past processing
        list_files = os.listdir(self.app_folder)
        for file in list_files:
            file_path = os.path.join(self.app_folder, file)
            if os.path.isdir(file_path) and 'img_th_processed' in file:
                self.proc_list.append(file)
                self.thermal_process_img_folders.append(os.path.join(self.app_folder, file))
            if os.path.isdir(file_path) and 'mesh_original' in file:
                self.rgb_mesh_done = True
            if os.path.isdir(file_path) and 'mesh_th' in file:
                self.th_mesh_folders.append(os.path.join(self.app_folder, file))

        # enable action
        self.pushButton_go_img.setEnabled(True)
        if self.proc_list:
            self.pushButton_go_mesh.setEnabled(True)

        if self.rgb_mesh_done:
            self.pushButton_go_visu.setEnabled(True)

        # update status
        self.update_progress("Status: You can now choose further processing!", 0)

    def go_img(self):
        # launch corresponding dialog
        dialog = dialog_prepare_images()
        apply_stylesheet(dialog, theme='light_blue.xml')
        dialog.setWindowTitle("Choose parameters for thermal images processing")

        if dialog.exec_():
            mode = 'other'  # alternative = 'averaged' --> The picture is normalized with min and max temperature detected on the picture
            try:
                tmin = float(dialog.lineEdit_min_temp.text())
                tmax = float(dialog.lineEdit_max_temp.text())  # Check if temps value are numbers
                i = dialog.comboBox.currentIndex()
                colormap = dialog.colormap_list[i]
                nummer = len(self.proc_list)

                desc = 'img_th_processed_' + colormap + '_' + str(round(tmin, 0)) + '_' \
                       + str(round(tmax, 0)) + '(image set ' + str(nummer) + ')'

                # append the processing to the list
                self.proc_list.append(desc)

                # launch image processing
                self.thermal_process_img_folders.append(os.path.join(self.app_folder, desc))
                os.mkdir(self.thermal_process_img_folders[-1])

                tt.process_all_th_pictures(self.original_th_img_folder, self.thermal_process_img_folders[-1], tmin, tmax, colormap, mode)

            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Warning",
                                              "Oops! A least one of the temperatures is not valit is no valid.  Try again...")
                self.go_img()

        # update buttons
        self.pushButton_go_mesh.setEnabled(True)

    def go_mesh(self):
        """
        Function called from the 3D processing button; will create 3D files from image sets
        """
        dialog = dialog_make_model()
        apply_stylesheet(dialog, theme='light_blue.xml')
        dialog.setWindowTitle("Choose 3d reconstruction parameters")

        # if no processing was ever done, then the user has no choice but doing 3D processing
        if not self.rgb_mesh_done:
            dialog.checkBox_model.setEnabled(False)
        else:
            dialog.checkBox_model.setEnabled(True)
            dialog.checkBox_model.setChecked(False)

        # fill list of process
        dialog.th_datasets_list = self.proc_list
        dialog.fill_comb()

        if dialog.exec_():
            # get reconstruction options
            i = dialog.img_set_index
            thermal_img_folder = self.thermal_process_img_folders[i]

            opt_texture = dialog.texture
            opt_quality = dialog.quality
            opt_masks = dialog.masked
            opt_ortho = dialog.ortho

            # new folders
            self.rgb_mesh_folder = os.path.join(self.app_folder, 'mesh_original')
            number = len(self.th_mesh_folders)
            desc = 'mesh_th_processed' + '(mesh ' + str(number) + ')'
            th_mesh_folder = os.path.join(self.app_folder, desc)
            self.th_mesh_folders.append(th_mesh_folder)

            # check if rgb model is needed
            if dialog.do_rec:
                if not os.path.exists(self.rgb_mesh_folder):
                    os.mkdir(self.rgb_mesh_folder)
                agisoft_part.make_rgb_mesh(self.rgb_img_folder, self.rgb_mesh_folder)
                self.rgb_mesh_done = True # change status, now a rgb mesh exists

            # do thermal processing
            if not os.path.exists(th_mesh_folder):
                os.mkdir(th_mesh_folder)
            agisoft_part.make_thermal_mesh(self.rgb_mesh_folder, thermal_img_folder, th_mesh_folder,
                                           opt_use_masks = opt_masks, opt_make_ortho = opt_ortho)

            # copy rgb texture to new folder _________________________


            # copy threejs folder to mesh location
            src = resources.find('threejs')
            dest = os.path.join(th_mesh_folder, 'threejs')
            copytree(src, dest)

    def go_visu(self):
        dialog = dialog_mesh_preview()
        apply_stylesheet(dialog, theme='light_blue.xml')
        dialog.set_folder_to_stream(self.mesh_folder)
        if dialog.exec_():
            pass

        """
        textured_mesh = o3d.io.read_triangle_mesh(mesh_file)
        print(textured_mesh)
        o3d.visualization.draw_geometries([textured_mesh])
        """





