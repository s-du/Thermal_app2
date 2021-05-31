Launch the following lines into pycharm python console to install Agisoft

________________________________
import pip

def install_whl(path):
    pip.main(['install', path])

install_whl(r'C:\Users\sdu\Desktop\Python 2021\Thermal V2\resources\other\Metashape-1.7.1-cp35.cp36.cp37.cp38-none-win_amd64.whl')
________________________________

pip install qt-material

________________________________

!! Add local license through environment variables
ex:
agisoft_LICENSE 
C:\Program Files\Agisoft\Metashape Pro\metashape2.lic
