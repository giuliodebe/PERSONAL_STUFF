import sys
import traceback
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QComboBox, QStackedWidget, 
                             QTextEdit, QTabWidget,QRadioButton,QButtonGroup,QSizePolicy)
from PyQt5.QtGui import QFont, QCloseEvent
from PyQt5.QtCore import Qt
from scipy.spatial.transform import Rotation as R
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Import the shared GUI functions
from GUI_settings import (set_dark_theme, set_light_theme, set_button_style, set_title_font,
                          set_common_stylesheet, set_input_field_style,
                          set_output_text_style, set_tab_widget_style)

class OrientationConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orientation Converter")
        self.resize(600, 800)
        self.setMinimumSize(int(600 * 0.9), int(800 * 0.9))
        self.setMaximumSize(int(600 * 1.2), int(800 * 1.2))
        
        self._theme = 'dark'
        self.visualization_window = None
        self.initUI()
        self.apply_theme()

    def initUI(self):   
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.title_label = QLabel("Orientation Converter")
        set_title_font(self.title_label)
        main_layout.addWidget(self.title_label)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(OriConverter(self), "Orientation Converter")
        self.tab_widget.addTab(AngleConverter(), "Angle Converter")
        main_layout.addWidget(self.tab_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def set_theme(self, theme):
        self._theme = theme
        self.apply_theme()
        
    def apply_theme(self):
        if self._theme == 'dark':
            set_dark_theme(self)
        else:
            set_light_theme(self)
        
        self.setStyleSheet(set_common_stylesheet(self._theme))
        set_tab_widget_style(self.tab_widget, self._theme)
        
        # Apply theme to child widgets
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme(self._theme)

    def closeEvent(self, event: QCloseEvent):
        if self.visualization_window:
            self.visualization_window.close()
        event.accept()

class VisualizationWindow(QMainWindow):
    """Separate window for visualization."""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Orientation Visualization')
        self.setGeometry(100, 100, 800, 600)
        self.setMaximumSize(1200, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.figure = plt.figure(figsize=(10, 5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

    def visualize(self, r: R):
        """Visualize the given rotation."""
        self.figure.clear()
        ax1 = self.figure.add_subplot(121, projection='3d')
        ax2 = self.figure.add_subplot(122, projection='3d')
        
        # Base coordinate system
        self.plot_coordinate_system(ax1, np.eye(3), "BASE COORDINATES")
        
        # Shifted coordinate system
        self.plot_coordinate_system(ax2, r.as_matrix(), "SHIFTED COORDINATES")
        
        self.figure.tight_layout()
        self.canvas.draw()
        self.show()

    def plot_coordinate_system(self, ax: plt.Axes, rotation_matrix: np.ndarray, title: str):
        """Plot a coordinate system on the given axes."""
        ax.quiver(0, 0, 0, *rotation_matrix[:, 0], color='r', label='X')
        ax.quiver(0, 0, 0, *rotation_matrix[:, 1], color='g', label='Y')
        ax.quiver(0, 0, 0, *rotation_matrix[:, 2], color='b', label='Z')
        
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.legend()
        ax.set_title(title)

    def closeEvent(self, event: QCloseEvent):
        # Hide the window instead of closing it
        event.ignore()
        self.hide()

class OriConverter(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.input_type = QComboBox()
        self.input_type.addItems(['Quaternion', 'Euler Angles', 'Rotation Matrix', 'Axis-Angle'])
        self.input_type.currentIndexChanged.connect(self.on_input_type_change)
        layout.addWidget(QLabel('Input Type:'))
        layout.addWidget(self.input_type)

        self.input_stack = QStackedWidget()
        self.input_stack.addWidget(self.create_input_widget('Quaternion'))
        self.input_stack.addWidget(self.create_input_widget('Euler Angles'))
        self.input_stack.addWidget(self.create_input_widget('Rotation Matrix'))
        self.input_stack.addWidget(self.create_input_widget('Axis-Angle'))
        layout.addWidget(self.input_stack)

        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton('CONVERT')
        self.convert_btn.clicked.connect(self.convert_orientation)
        button_layout.addWidget(self.convert_btn)

        self.visualize_btn = QPushButton('SHOW VISUALIZATION')
        self.visualize_btn.clicked.connect(self.show_visualization)
        button_layout.addWidget(self.visualize_btn)

        layout.addLayout(button_layout)

        self.output_tabs = QTabWidget()
        self.quaternion_output = QTextEdit()
        self.euler_output = QTextEdit()
        self.rotation_matrix_output = QTextEdit()
        self.axis_angle_output = QTextEdit()
        
        self.output_tabs.addTab(self.quaternion_output, "Quaternion")
        self.output_tabs.addTab(self.euler_output, "Euler Angles")
        self.output_tabs.addTab(self.rotation_matrix_output, "Rotation Matrix")
        self.output_tabs.addTab(self.axis_angle_output, "Axis-Angle")
        
        layout.addWidget(self.output_tabs)

        self.setLayout(layout)

    def create_input_widget(self, input_type):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if input_type == 'Quaternion':
            default_values = ['1', '0', '0', '0']  # w, x, y, z
            for label, default_value in zip(['w', 'x', 'y', 'z'], default_values):
                input_field = QLineEdit(default_value)
                layout.addWidget(QLabel(f'{label}:'))
                layout.addWidget(input_field)
        elif input_type == 'Euler Angles':
            default_values = ['0', '0', '0']  # z, y, x in degrees
            self.euler_unit = QButtonGroup(widget)
            rad_button = QRadioButton("Radians")
            deg_button = QRadioButton("Degrees")
            deg_button.setChecked(True)
            self.euler_unit.addButton(rad_button)
            self.euler_unit.addButton(deg_button)
            layout.addWidget(rad_button)
            layout.addWidget(deg_button)
            for label, default_value in zip(['z', 'y', 'x'], default_values):
                input_field = QLineEdit(default_value)
                layout.addWidget(QLabel(f'{label}:'))
                layout.addWidget(input_field)
        elif input_type == 'Rotation Matrix':
            default_values = [['1', '0', '0'], ['0', '1', '0'], ['0', '0', '1']]  # Identity matrix
            for i in range(3):
                row_layout = QHBoxLayout()
                for j in range(3):
                    input_field = QLineEdit(default_values[i][j])
                    row_layout.addWidget(input_field)
                layout.addLayout(row_layout)
        elif input_type == 'Axis-Angle':
            default_values = ['0', '0', '0']  # z, y, x rotations
            self.axis_angle_unit = QButtonGroup(widget)
            rad_button = QRadioButton("Radians")
            deg_button = QRadioButton("Degrees")
            deg_button.setChecked(True)
            self.axis_angle_unit.addButton(rad_button)
            self.axis_angle_unit.addButton(deg_button)
            layout.addWidget(rad_button)
            layout.addWidget(deg_button)
            for label, default_value in zip(['z', 'y', 'x'], default_values):
                input_field = QLineEdit(default_value)
                layout.addWidget(QLabel(f'Rotation around {label}:'))
                layout.addWidget(input_field)
        
        return widget
    
    def on_input_type_change(self, index):
        self.input_stack.setCurrentIndex(index)

    def convert_orientation(self):
        print("Convert button clicked")  # Debug print
        input_type = self.input_type.currentText()
        input_widget = self.input_stack.currentWidget()
        input_data = [float(child.text()) for child in input_widget.findChildren(QLineEdit)]
        print(f"Input type: {input_type}")  # Debug print
        print(f"Input data: {input_data}")  # Debug print

        try:
            rotation = self.create_rotation(input_type, input_data)
            self.update_outputs(rotation, input_type, input_data)
            self.current_rotation = rotation
        except Exception as e:
            print(f"Error in conversion: {str(e)}")  # Debug print
            logging.error(f"Error in OrientationConverter.convert_orientation: {str(e)}")
            logging.debug(traceback.format_exc())

    def create_rotation(self, input_type, input_data):
        if input_type == 'Quaternion':
            w, x, y, z = input_data
            return R.from_quat([x, y, z, w])
        elif input_type == 'Euler Angles':
            is_degrees = self.euler_unit.checkedButton().text() == "Degrees"
            if is_degrees:
                return R.from_euler('zyx', np.radians(input_data))
            else:
                return R.from_euler('zyx', input_data)
        elif input_type == 'Rotation Matrix':
            return R.from_matrix(np.array(input_data).reshape((3, 3)))
        elif input_type == 'Axis-Angle':
            is_degrees = self.axis_angle_unit.checkedButton().text() == "Degrees"
            if is_degrees:
                return R.from_euler('zyx', np.radians(input_data))
            else:
                return R.from_euler('zyx', input_data)

    def update_outputs(self, rotation, input_type, input_data):
        print("Updating outputs")  # Debug print
        quat = rotation.as_quat()
        euler_deg = rotation.as_euler('zyx', degrees=True)
        euler_rad = rotation.as_euler('zyx', degrees=False)
        matrix = rotation.as_matrix()
        rotvec = rotation.as_rotvec()

        self.update_quaternion_output(quat)
        self.update_euler_output(euler_deg, euler_rad)
        self.update_matrix_output(matrix)
        self.update_axis_angle_output(rotvec)

    def update_quaternion_output(self, quat):
        output = (f"<b>Quaternion [w, x, y, z]:</b><br>"
                  f"w: {quat[3]:.6f}<br>x: {quat[0]:.6f}<br>y: {quat[1]:.6f}<br>z: {quat[2]:.6f}")
        self.quaternion_output.setHtml(output)
        print("Quaternion output updated")  # Debug print

    def update_euler_output(self, euler_deg, euler_rad):
        output = (f"<b>Euler Angles (zyx order):</b><br>"
                  f"Degrees:<br>z: {euler_deg[0]:.6f}°<br>y: {euler_deg[1]:.6f}°<br>x: {euler_deg[2]:.6f}°<br><br>"
                  f"Radians:<br>z: {euler_rad[0]:.6f}<br>y: {euler_rad[1]:.6f}<br>x: {euler_rad[2]:.6f}")
        self.euler_output.setHtml(output)
        print("Euler output updated")  # Debug print

    def update_matrix_output(self, matrix):
        output = "<b>Rotation Matrix:</b><br>["
        for i, row in enumerate(matrix):
            if i > 0:
                output += " "
            output += " ".join(f"{val:10.6f}" for val in row)
            if i < 2:
                output += "<br>"
        output += "]"
        self.rotation_matrix_output.setHtml(output)
        print("Matrix output updated")  # Debug print

    def update_axis_angle_output(self, rotvec):
        angle = np.linalg.norm(rotvec)
        axis = rotvec / angle if angle != 0 else np.array([0, 0, 1])
        angle_deg = np.degrees(angle)
        
        output = (f"<b>Axis-Angle Representation:</b><br>"
                  f"<b>Axis:</b> [{axis[0]:.6f}, {axis[1]:.6f}, {axis[2]:.6f}]<br>"
                  f"<b>Angle:</b> {angle_deg:.6f}° ({angle:.6f} radians)<br><br>"
                  f"<b>Equivalent Euler Angles (zyx order):</b><br>"
                  f"<b>Degrees:</b><br>"
                  f"z: {np.degrees(rotvec[2]):.6f}°<br>"
                  f"y: {np.degrees(rotvec[1]):.6f}°<br>"
                  f"x: {np.degrees(rotvec[0]):.6f}°<br><br>"
                  f"<b>Radians:</b><br>"
                  f"z: {rotvec[2]:.6f}<br>"
                  f"y: {rotvec[1]:.6f}<br>"
                  f"x: {rotvec[0]:.6f}")
        self.axis_angle_output.setHtml(output)
        print("Axis-Angle output updated")  # Debug print

    def apply_theme(self, theme):
        set_input_field_style(self.input_type, theme)
        set_button_style(self.convert_btn, theme)
        set_tab_widget_style(self.output_tabs, theme)
        for output in [self.quaternion_output, self.euler_output, self.rotation_matrix_output, self.axis_angle_output]:
            set_output_text_style(output, theme)
        
        # Apply theme to radio buttons
        for widget in self.findChildren(QRadioButton):
            set_input_field_style(widget, theme)

    def show_visualization(self):
        if self.parent.visualization_window is None:
            self.parent.visualization_window = VisualizationWindow()
        
        if hasattr(self, 'current_rotation'):
            self.parent.visualization_window.visualize(self.current_rotation)
            self.parent.visualization_window.show()
        else:
            logging.warning("No rotation data available for visualization.")

class AngleConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        input_layout = QHBoxLayout()
        self.input_angle = QLineEdit()
        self.input_angle.setFixedWidth(200)
        input_layout.addWidget(QLabel('Input Angle:'))
        input_layout.addWidget(self.input_angle)
        layout.addLayout(input_layout)

        type_layout = QHBoxLayout()
        self.input_type = QComboBox()
        self.input_type.addItems(['Degrees', 'Radians'])
        self.input_type.setFixedWidth(200)
        type_layout.addWidget(QLabel('Input Type:'))
        type_layout.addWidget(self.input_type)
        layout.addLayout(type_layout)

        self.convert_btn = QPushButton('CONVERT')
        self.convert_btn.clicked.connect(self.convert_angle)
        layout.addWidget(self.convert_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def convert_angle(self):
        try:
            angle = float(self.input_angle.text())
            if self.input_type.currentText() == 'Degrees':
                degrees = angle
                radians = np.radians(angle)
            else:
                radians = angle
                degrees = np.degrees(angle)
            
            output_text = "<b>Conversion Result:</b><br>"
            output_text += f"<b>Degrees:</b> {degrees:.6f}°<br>"
            output_text += f"<b>Radians:</b> {radians:.6f}"
            self.output.setHtml(output_text)
        except ValueError:
            self.output.setHtml("Error: Invalid input")
        except Exception as e:
            self.output.setHtml(f"Error: {str(e)}")
            logging.error(f"Error in AngleConverter.convert_angle: {str(e)}")
            logging.debug(traceback.format_exc())

    def apply_theme(self, theme):
        set_input_field_style(self.input_angle, theme)
        set_input_field_style(self.input_type, theme)
        set_button_style(self.convert_btn, theme)
        set_output_text_style(self.output, theme)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = OrientationConverter()
    main_app.show()
    sys.exit(app.exec_())