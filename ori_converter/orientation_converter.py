import sys
import traceback
import logging
from typing import List, Tuple, Union
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QStackedWidget, QTextEdit, 
                             QTabWidget, QGridLayout, QMainWindow,QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCloseEvent
from scipy.spatial.transform import Rotation as R
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class InputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMaximumHeight(200)  # Limit the height of input widgets

    def create_input_fields(self, labels: List[str], default_value: str = "0") -> List[QLineEdit]:
        fields = [QLineEdit(default_value) for _ in labels]
        for field in fields:
            field.setAlignment(Qt.AlignRight)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field.setMaximumWidth(150)  # Limit the width of input fields
        return fields

class QuaternionInput(InputWidget):
    """Widget for Quaternion input."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = self.create_input_fields(['w', 'x', 'y', 'z'], "0")
        self.inputs[1].setText("0")  # Set x, y, z to 0 by default
        self.inputs[2].setText("0")
        self.inputs[3].setText("1")
        for i, (label, input_field) in enumerate(zip(['w', 'x', 'y', 'z'], self.inputs)):
            self.layout.addWidget(QLabel(f'{label}:'), i, 0)
            self.layout.addWidget(input_field, i, 1)

    def get_data(self) -> np.ndarray:
        return np.array([float(input.text()) for input in self.inputs])

class EulerAnglesInput(InputWidget):
    """Widget for Euler Angles input."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = self.create_input_fields(['Roll', 'Pitch', 'Yaw'])
        for i, (label, input_field) in enumerate(zip(['Roll', 'Pitch', 'Yaw'], self.inputs)):
            self.layout.addWidget(QLabel(f'{label}:'), i, 0)
            self.layout.addWidget(input_field, i, 1)
        self.units = QComboBox()
        self.units.addItems(['Radians', 'Degrees'])
        self.layout.addWidget(QLabel('Units:'), 3, 0)
        self.layout.addWidget(self.units, 3, 1)

    def get_data(self) -> np.ndarray:
        data = np.array([float(input.text()) for input in self.inputs])
        if self.units.currentText() == 'Degrees':
            data = np.radians(data)
        return data

class RotationMatrixInput(InputWidget):
    """Widget for Rotation Matrix input."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = [self.create_input_fields([''] * 3) for _ in range(3)]
        for i in range(3):
            for j in range(3):
                if i == j:
                    self.inputs[i][j].setText("1")  # Set diagonal elements to 1
                self.layout.addWidget(self.inputs[i][j], i, j)

    def get_data(self) -> np.ndarray:
        return np.array([[float(input.text()) for input in row] for row in self.inputs])

class AxisAngleInput(InputWidget):
    """Widget for Axis-Angle input with separate angles for each axis."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = self.create_input_fields(['X Rotation', 'Y Rotation', 'Z Rotation'])
        for i, (label, input_field) in enumerate(zip(['X Rotation', 'Y Rotation', 'Z Rotation'], self.inputs)):
            self.layout.addWidget(QLabel(f'{label}:'), i, 0)
            self.layout.addWidget(input_field, i, 1)
        self.units = QComboBox()
        self.units.addItems(['Radians', 'Degrees'])
        self.layout.addWidget(QLabel('Angle Units:'), 3, 0)
        self.layout.addWidget(self.units, 3, 1)

    def get_data(self) -> np.ndarray:
        data = np.array([float(input.text()) for input in self.inputs])
        if self.units.currentText() == 'Degrees':
            data = np.radians(data)
        return data
    
class AngleConverter(QWidget):
    """Widget for converting between degrees and radians."""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Angle Converter')
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QLineEdit, QTextEdit { background-color: #3b3b3b; border: 1px solid #555555; }
            QPushButton { background-color: #1565c0; padding: 5px; }
            QPushButton:hover { background-color: #1000c0; }
            QComboBox { background-color: #3b3b3b; border: 1px solid #555555; padding: 5px; }
            QTabBar::tab { background-color: #1000c10c10c; color: #000309; }
            QTabBar::tab:selected { background-color: #800c; }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Input
        input_layout = QHBoxLayout()
        input_layout.addStretch()
        self.input_angle = QLineEdit()
        self.input_angle.setFixedWidth(200)
        input_layout.addWidget(QLabel('Input Angle:'))
        input_layout.addWidget(self.input_angle)
        layout.addLayout(input_layout)
        input_layout.addStretch()
        layout.addLayout(input_layout)

        # Input type
        type_layout = QHBoxLayout()
        type_layout.addStretch()
        self.input_type = QComboBox()
        self.input_type.addItems(['Degrees', 'Radians'])
        self.input_type.setFixedWidth(200)
        type_layout.addWidget(QLabel('Input Type:'))
        type_layout.addWidget(self.input_type)
        layout.addLayout(type_layout)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Convert button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.convert_btn = QPushButton('CONVERT')
        self.convert_btn.clicked.connect(self.convert)
        self.convert_btn.setFixedWidth(150)
        button_layout.addWidget(self.convert_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)


        # Label layout
        label_layout = QHBoxLayout()
        label_layout.addStretch()

        self.output_label = QLabel('OUTPUT:')
        self.output_label.setAlignment(Qt.AlignCenter)
        label_layout.addWidget(self.output_label)
        label_layout.addStretch()
        layout.addLayout(label_layout)
        
        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.output.setMaximumHeight(200)  # Limit the height of the output tabs
        layout.addWidget(self.output)

        self.setLayout(layout)

    def convert(self):
        try:
            angle = float(self.input_angle.text())
            if self.input_type.currentText() == 'Degrees':
                radians = np.radians(angle)
                degrees = angle
            else:
                radians = angle
                degrees = np.degrees(angle)
            
            output_text = f"Degrees: {degrees:.6f}\n"
            output_text += f"Radians: {radians:.6f}"
            self.output.setText(output_text)
        except ValueError:
            self.output.setText("Error: Invalid input")
        except Exception as e:
            logging.error(f"Error in AngleConverter.convert: {str(e)}")
            logging.debug(traceback.format_exc())

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

class OrientationConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.visualization_window = VisualizationWindow()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Orientation Converter')
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QLineEdit, QTextEdit { background-color: #3b3b3b; border: 1px solid #555555; }
            QPushButton { background-color: #1565c0; padding: 5px; }
            QPushButton:hover { background-color: #1000c0; }
            QComboBox { background-color: #3b3b3b; border: 1px solid #555555; padding: 5px; }
            QTabBar::tab { background-color: #1000c10c10c; color: #000309; }
            QTabBar::tab:selected { background-color: #800c; }
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tab_widget.addTab(self.create_converter_tab(), "ORIENTATION CONVERTER")
        self.tab_widget.addTab(AngleConverter(), "ANGLE CONVERTER")
        layout.addWidget(self.tab_widget)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(450, 300)  # Set a minimum size for the main window
        self.setMaximumSize(500, 600)  # Set a maximum size for the main window

    def create_converter_tab(self) -> QWidget:
            converter_widget = QWidget()
            layout = QVBoxLayout()

            # Input type selection
            input_type_layout = QHBoxLayout()
            input_type_layout.addStretch()
            self.input_type = QComboBox()
            self.input_type.addItems(['Quaternion', 'Euler Angles', 'Rotation Matrix', 'Axis-Angle'])
            self.input_type.currentIndexChanged.connect(self.on_input_type_change)
            self.input_type.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.input_type.setFixedWidth(200)
            input_type_layout.addWidget(QLabel('Input Type:'))
            input_type_layout.addWidget(self.input_type)
            input_type_layout.addStretch()
            layout.addLayout(input_type_layout)

            # Stacked widget for different input types
            input_stack_layout = QHBoxLayout()
            input_stack_layout.addStretch()
            self.input_stack = QStackedWidget()
            self.input_stack.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.input_stack.setFixedSize(300, 200)  # Adjust size as needed
            self.input_stack.addWidget(QuaternionInput())
            self.input_stack.addWidget(EulerAnglesInput())
            self.input_stack.addWidget(RotationMatrixInput())
            self.input_stack.addWidget(AxisAngleInput())
            input_stack_layout.addWidget(self.input_stack)
            input_stack_layout.addStretch()
            layout.addLayout(input_stack_layout)

            # Buttons
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.convert_btn = QPushButton('CONVERT')
            self.convert_btn.clicked.connect(self.convert)
            self.convert_btn.setFixedWidth(150)
            button_layout.addWidget(self.convert_btn)

            button_layout.addSpacing(20)  # Add some space between buttons

            self.visualize_btn = QPushButton('SHOW VISUALIZATION')
            self.visualize_btn.clicked.connect(self.show_visualization)
            self.visualize_btn.setFixedWidth(150)
            button_layout.addWidget(self.visualize_btn)

            button_layout.addStretch()
            layout.addLayout(button_layout)

            # Output
            self.output_tabs = QTabWidget()
            self.output_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.output_tabs.setMaximumHeight(200)  # Limit the height of the output tabs
            self.output_tabs.addTab(self.create_output_tab("QUATERNION"), "QUATERNION")
            self.output_tabs.addTab(self.create_output_tab("EULER_ANGLES"), "EULER ANGLES")
            self.output_tabs.addTab(self.create_output_tab("ROTATION_MATRIX"), "ROTATION MATRIX")
            self.output_tabs.addTab(self.create_output_tab("AXIS_ANGLE"), "AXIS-ANGLE")
            layout.addWidget(self.output_tabs)

            converter_widget.setLayout(layout)
            return converter_widget
    
    def show_visualization(self):
        if self.visualization_window is None:
            self.visualization_window = VisualizationWindow()
        
        if hasattr(self, 'current_rotation'):
            self.visualization_window.visualize(self.current_rotation)
            self.visualization_window.show()
        else:
            logging.warning("No rotation data available for visualization.")

    def closeEvent(self, event: QCloseEvent):
        # Close the visualization window if it exists
        if self.visualization_window:
            self.visualization_window.close()
        event.accept()

    def create_output_tab(self, title: str) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        output = QTextEdit()
        output.setReadOnly(True)
        output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        font = QFont()
        font.setPointSize(12)
        output.setFont(font)
        layout.addWidget(output)
        tab.setLayout(layout)
        attr_name = f"{title.lower()}_output"
        setattr(self, attr_name, output)
        return tab

    def on_input_type_change(self, index: int):
        """Handle changes in the input type selection."""
        self.input_stack.setCurrentIndex(index)

    def get_input_data(self) -> np.ndarray:
        """Get the input data from the current input widget."""
        return self.input_stack.currentWidget().get_data()

    def convert(self):
        """Convert the input data to all other representations."""
        input_type = self.input_type.currentText()
        try:
            input_data = self.get_input_data()

            if input_type == 'Quaternion':
                r = R.from_quat(input_data)
            elif input_type == 'Euler Angles':
                r = R.from_euler('xyz', input_data)
            elif input_type == 'Rotation Matrix':
                r = R.from_matrix(input_data)
            elif input_type == 'Axis-Angle':
                r = R.from_euler('xyz', input_data)

            quat = r.as_quat()
            euler = r.as_euler('xyz')
            matrix = r.as_matrix()
            rotvec = r.as_rotvec()

            # Quaternion output
            self.quaternion_output.setText(f"w: {quat[0]:.6f}\nx: {quat[1]:.6f}\ny: {quat[2]:.6f}\nz: {quat[3]:.6f}")
            
            # Euler angles output
            self.euler_angles_output.setText(f"Radians:\nRoll: {euler[0]:.6f}\nPitch: {euler[1]:.6f}\nYaw: {euler[2]:.6f}\n\n"
                                             f"Degrees:\nRoll: {np.degrees(euler[0]):.6f}\nPitch: {np.degrees(euler[1]):.6f}\nYaw: {np.degrees(euler[2]):.6f}")
           
            # Rotation matrix output
            matrix_output  = "⎡                              ⎤   ⎡   ⎤\n"
            matrix_output += "⎢ {:8.4f}  {:8.4f}  {:8.4f} ⎥ → ⎢ x ⎥\n".format(matrix[0, 0], matrix[0, 1], matrix[0, 2])
            matrix_output += "⎢ {:8.4f}  {:8.4f}  {:8.4f} ⎥ → ⎢ y ⎥\n".format(matrix[1, 0], matrix[1, 1], matrix[1, 2])
            matrix_output += "⎢ {:8.4f}  {:8.4f}  {:8.4f} ⎥ → ⎢ z ⎥\n".format(matrix[2, 0], matrix[2, 1], matrix[2, 2])
            matrix_output += "⎣                              ⎦   ⎣   ⎦\n"
            matrix_output += "     ↓         ↓         ↓\n"
            matrix_output += "     x         y         z"
            self.rotation_matrix_output.setFont(QFont("Courier"))
            self.rotation_matrix_output.setText(matrix_output)

            # Axis-angle output
            angle = np.linalg.norm(rotvec)
            axis = rotvec / angle if angle != 0 else np.array([0, 0, 1])
            x_rotation, y_rotation, z_rotation = euler
            self.axis_angle_output.setText(
                f"Combined Axis-Angle:\n"
                f"Axis: x: {axis[0]:.6f}, y: {axis[1]:.6f}, z: {axis[2]:.6f}\n"
                f"Angle (rad): {angle:.6f}\n"
                f"Angle (deg): {np.degrees(angle):.6f}\n\n"
                f"Separate Axis Rotations:\n"
                f"Radians:\n"
                f"X: {x_rotation:.6f}\n"
                f"Y: {y_rotation:.6f}\n"
                f"Z: {z_rotation:.6f}\n\n"
                f"Degrees:\n"
                f"X: {np.degrees(x_rotation):.6f}\n"
                f"Y: {np.degrees(y_rotation):.6f}\n"
                f"Z: {np.degrees(z_rotation):.6f}"
                  )

            # Store the current rotation for visualization
            self.current_rotation = r

        except Exception as e:
            error_message = f"Error: {str(e)}"
            logging.error(f"Error in OrientationConverter.convert: {error_message}")
            logging.debug(traceback.format_exc())
            for output in [self.quaternion_output, self.euler_angles_output, self.rotation_matrix_output, self.axis_angle_output]:
                output.setText(error_message)

    def show_visualization(self):
        """Show the visualization in a separate window."""
        if hasattr(self, 'current_rotation'):
            self.visualization_window.visualize(self.current_rotation)
        else:
            logging.warning("No rotation data available for visualization.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OrientationConverter()
    ex.show()
    sys.exit(app.exec_())
