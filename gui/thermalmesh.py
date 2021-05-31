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
from tools import flir_image_extractor
from tools import agisoft_part
fir = flir_image_extractor.FlirImageExtractor()

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

        # define useful paths
        self.gui_folder = os.path.dirname(__file__)

        self.image_processed = False
        self.mesh_created = False

        # Initialize combobox
        pixmap = QtGui.QPixmap("files/plasma.png")
        pixmap = pixmap.scaledToWidth(200)
        self.label_thumb.setPixmap(pixmap)
        self.label_thumb.show()

        # Initialize status
        self.update_progress("Status: Define folder!", 0)

        # Create connections (signals)
        self.create_connections()


    def create_connections(self):

        # 'Simplify buttons'
        self.pushButton_load.clicked.connect(self.load)
        self.pushButton_go_img.clicked.connect(self.go_img)
        self.pushButton_go_mesh.clicked.connect(self.go_mesh)
        self.pushButton_go_visu.clicked.connect(self.go_visu)
        self.comboBox.currentIndexChanged.connect(self.on_combo_changed)

    def update_progress(self, text, nb):
        self.label_status.setText(text)
        self.progressBar.setProperty("value", nb)


    def load(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

        if not folder == "": # If user cancel selection, stop function

            # Define path
            self.folder = folder
            self.mesh_folder = os.path.join(self.folder, 'meshes')
            self.label_folder.setText(str(self.folder))

            # Enable actions for user
            self.lineEdit_min_temp.setEnabled(True)
            self.lineEdit_max_temp.setEnabled(True)
            self.comboBox.setEnabled(True)
            self.pushButton_go_img.setEnabled(True)
            self.pushButton_go_mesh.setEnabled(True)
            self.pushButton_go_visu.setEnabled(True)

            # Fill combobox with colormaps choices
            self.colormap_list = ['plasma', 'inferno', 'Greys', 'Greys_r', 'coolwarm', 'jet', 'rainbow', 'Spectral_r']
            self.comboBox.addItems(self.colormap_list)

            self.update_progress("Status: Choose colormap and temp's", 0)

    def go_img(self):
        # Collect reconstruction parameters
        mode = 'other'  # alternative = 'averaged' --> The picture is normalized with min and max temperature detected on the picture

        try:
            tmin = float(self.lineEdit_min_temp.text())
            tmax = float(self.lineEdit_max_temp.text())  # Check if temps value are numbers
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Warning", "Oops! A least one of the temperatures is not valit is no valid.  Try again...")
            return

        masked = self.checkBox_masks.isChecked()
        i = self.comboBox.currentIndex()
        colormap = self.colormap_list[i]
        print(colormap)

        # Images folders creation
        img_folder = self.folder
        # sorting images in subfolders
        self.thermal_process_img_folder = os.path.join(img_folder, 'thermal_processed')
        self.rgb_img_folder = os.path.join(img_folder, 'rgb')

        if not os.path.exists(self.thermal_process_img_folder):
            os.mkdir(self.thermal_process_img_folder)
        if not os.path.exists(self.rgb_img_folder):
            os.mkdir(self.rgb_img_folder)

        # Sorting images in new folders
        i=1
        for file in os.listdir(img_folder):
            print(file)

            new_file = 'image_' + str(i) + '.jpg'
            if file.endswith('.jpg'):
                copyfile(os.path.join(img_folder, file), os.path.join(self.rgb_img_folder, new_file))
                i += 1

            elif file.endswith('R.JPG'):
                copyfile(os.path.join(img_folder, file), os.path.join(self.thermal_process_img_folder, new_file))
                new_path = os.path.join(self.thermal_process_img_folder, new_file)
                fir.process_image(new_path)
                fir.save_images(tmin, tmax, colormap, mode)

                to_remove_file = new_file[:-4] + '_rgb_thumb.jpg'
                os.remove(os.path.join(self.thermal_process_img_folder, to_remove_file))
                os.remove(new_path)

        # update buttons
        self.image_processed = True


    def go_mesh(self):

        if not os.path.exists(self.mesh_folder):
            os.mkdir(self.mesh_folder)

        if self.image_processed:
            rgb_folder = self.rgb_img_folder
            thermal_folder = self.thermal_process_img_folder
        else:
            rgb_folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory with RGB images"))
            thermal_folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory with Thermal images"))

        agisoft_part.make_thermal_mesh(False, self.mesh_folder, rgb_folder, thermal_folder)

        # launch mesh preview

        mesh_file = os.path.join(self.main_folder, 'mesh_thermal1.obj')
        text_file = os.path.join(self.main_folder, 'mesh_thermal1.jpg')

        # copy threejs folder to mesh location
        src = resources.find('threejs')
        dest = os.path.join(self.mesh_folder, 'threejs')
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




    def on_combo_changed(self):
        i = self.comboBox.currentIndex()
        img_thumb_list = ['plasma.png', 'inferno.png', 'greys.png', 'greys_r.png', 'coolwarm.png', 'jet.png', 'rainbow.png', 'spectral_r.png']
        to_find = 'img/' + img_thumb_list[i]
        pixmap = QtGui.QPixmap(resources.find(to_find))
        pixmap = pixmap.scaledToWidth(200)
        self.label_thumb.setPixmap(pixmap)
        self.label_thumb.show()
