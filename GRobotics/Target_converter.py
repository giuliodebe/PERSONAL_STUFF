import sys
import pyperclip
import re
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFormLayout,
                             QDialog, QDialogButtonBox, QListWidget, QComboBox, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPalette, QColor, QTextCharFormat
from PyQt5.QtCore import Qt, pyqtSignal
from scipy.spatial.transform import Rotation

from GUI_settings import (set_dark_theme, set_button_style, set_title_font,
                          set_common_stylesheet, set_input_field_style,
                          set_output_text_style, set_tab_widget_style, set_light_theme)

def quaternion_to_rotation_matrix(quat):
    """Convert a quaternion into a rotation matrix."""
    return Rotation.from_quat(quat).as_matrix()

def apply_transformation(position, rotation_quat, translation, rotation_quat_cs):
    """Applies transformation (rotation and translation) on a given robtarget."""
    rotation_matrix_robtarget = quaternion_to_rotation_matrix(rotation_quat)
    rotation_matrix_cs = quaternion_to_rotation_matrix(rotation_quat_cs)
    transformed_position = np.dot(rotation_matrix_cs, position) + translation
    rotation_combined = Rotation.from_quat(rotation_quat_cs) * Rotation.from_quat(rotation_quat)
    transformed_rotation_quat = rotation_combined.as_quat()
    return transformed_position, transformed_rotation_quat

def invert_transformation(translation, rotation_quat):
    """Inverts a transformation (reverse rotation and translation)."""
    inverted_rotation_quat = Rotation.from_quat(rotation_quat).inv().as_quat()
    inverted_rotation_matrix = quaternion_to_rotation_matrix(inverted_rotation_quat)
    inverted_translation = -np.dot(inverted_rotation_matrix, translation)
    return inverted_translation, inverted_rotation_quat

def transform_robtarget(robtarget, input_coord_system, output_coord_system):
    """Transforms a robtarget from one coordinate system to another."""
    position = np.array(robtarget[0], dtype=float)
    orientation = np.array(robtarget[1], dtype=float)
    robot_config = robtarget[2]
    external_axis = robtarget[3]

    input_position = np.array(input_coord_system['position'], dtype=float)
    input_orientation = Rotation.from_quat(input_coord_system['orientation'])
    output_position = np.array(output_coord_system['position'], dtype=float)
    output_orientation = Rotation.from_quat(output_coord_system['orientation'])

    inv_input_translation, inv_input_quat = invert_transformation(input_position, input_orientation.as_quat())
    position_in_world, quat_in_world = apply_transformation(
        position, orientation, inv_input_translation, inv_input_quat
    )

    final_position, final_quat = apply_transformation(
        position_in_world, quat_in_world, output_position, output_orientation.as_quat()
    )

    transformed_robtarget = [
        final_position.tolist(),
        final_quat.tolist(),
        robot_config,
        external_axis
    ]

    return transformed_robtarget

def format_robtarget(robtarget):
    """Formats the robtarget for display."""
    position = [f"{x:.2f}" for x in robtarget[0]]
    orientation = [f"{x:.6f}" for x in robtarget[1]]
    robot_config = [str(int(x)) for x in robtarget[2]]
    external_axis = [f"{x:.2f}" if abs(x - 9e9) >= 1e-6 else "9E+09" for x in robtarget[3]]
    
    return (f"[[{', '.join(position)}], [{', '.join(orientation)}], "
            f"[{', '.join(robot_config)}], [{', '.join(external_axis)}]]")

class CoordinateSystemInputWindow(QDialog):
    coordinateSystemsAdded = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Coordinate Systems")
        self.setModal(True)
        
        # Set the initial size
        self.resize(600, 400)
        
        # Calculate and set the maximum size (20% larger)
        max_width = int(self.width() * 1.2)
        max_height = int(self.height() * 1.2)
        self.setMaximumSize(max_width, max_height)
        
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter coordinate systems (one per line) in the format:\n"
                                          "TASK PERS wobjdata Name :=[FALSE,TRUE,[[x,y,z],[qw,qx,qy,qz]]];")
        layout.addWidget(self.text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.add_coordinate_systems)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
 
    def add_coordinate_systems(self):
        """Adds coordinate systems entered in the text edit to the application."""
        input_text = self.text_edit.toPlainText().strip()
        coord_systems = {}
        for line in input_text.split('\n'):
            match = re.match(r'TASK\s+PERS\s+wobjdata\s+(\w+)\s*:=\s*\[.*?\[\[([-\d.]+),([-\d.]+),([-\d.]+)\],\[([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)\]\]', line.strip())
            if match:
                name = match.group(1)
                position = [float(match.group(2)), float(match.group(3)), float(match.group(4))]
                orientation = [float(match.group(5)), float(match.group(6)), float(match.group(7)), float(match.group(8))]
                coord_systems[name] = {'position': position, 'orientation': orientation}
        
        if coord_systems:
            self.coordinateSystemsAdded.emit(coord_systems)
            self.accept()
        else:
            print("No valid coordinate systems found. Please check the format and try again.")

    def set_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet(set_common_stylesheet('dark'))
            set_input_field_style(self.text_edit, 'dark')
        else:
            self.setStyleSheet(set_common_stylesheet('light'))
            set_input_field_style(self.text_edit, 'light')

class InputWindow(QDialog):
    inputUpdated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Multiple Targets")
        self.setModal(True)
        
        # Set the initial size
        self.resize(600, 400)
        
        # Calculate and set the maximum size (20% larger)
        max_width = int(self.width() * 1.2)
        max_height = int(self.height() * 1.2)
        self.setMaximumSize(max_width, max_height)
        
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter targets here (one per line)\n"
                                          "Format: [LOCAL] [CONST] robtarget TargetName := [[x,y,z],[qw,qx,qy,qz],[cfg],[ext]];")
        layout.addWidget(self.text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.apply_input)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

    def apply_input(self):
        input_text = self.text_edit.toPlainText()
        #print("Input text in InputWindow:", input_text)  # Debug print
        self.inputUpdated.emit(input_text)
        self.accept()
    
    def set_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet(set_common_stylesheet('dark'))
            set_input_field_style(self.text_edit, 'dark')
        else:
            self.setStyleSheet(set_common_stylesheet('light'))
            set_input_field_style(self.text_edit, 'light')

class TargetConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_theme = 'light'  # Default theme
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        self.setWindowTitle("Target Converter")
        self.setGeometry(100, 100, 400, 300)
        
        # Calculate and set the maximum size (20% larger)
        max_width = int(self.width() * 1.2)
        max_height = int(self.height() * 1.2)
        self.setMaximumSize(max_width, max_height)
        
        self.label = QLabel("")
        self.coordinate_systems = {
            'Wobj0': {'position': [0, 0, 0], 'orientation': [1, 0, 0, 0]}
        }
        
        self.robtarget_data = {}
        self.converted_data = {}
        
        # Title
        title_label = QLabel("Robtarget Converter")
        set_title_font(title_label)
        main_layout.addWidget(title_label)
        
        #Form Layout
        form_layout = QFormLayout()

        self.input_cs_combo = QComboBox()
        self.input_cs_combo.addItems(self.coordinate_systems.keys())
        form_layout.addRow("Input Coordinate System", self.input_cs_combo)
        
        self.output_cs_combo = QComboBox()
        self.output_cs_combo.addItems(self.coordinate_systems.keys())
        form_layout.addRow("Output Coordinate System", self.output_cs_combo)
        
        main_layout.addLayout(form_layout)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        
        add_coord_button = QPushButton("Add Coordinate System")
        set_button_style(add_coord_button)
        add_coord_button.clicked.connect(self.show_coordinate_system_window)
        button_layout.addWidget(add_coord_button)

        add_robtarget_button = QPushButton("Input Multiple Robtargets")
        set_button_style(add_robtarget_button)
        add_robtarget_button.clicked.connect(self.show_input_window)
        button_layout.addWidget(add_robtarget_button)

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)
        
        # Add label for input robtargets
        input_label = QLabel("INPUT ROBTARGETS")
        input_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(input_label)
        
        self.robtarget_input = QListWidget()
        set_input_field_style(self.robtarget_input)
        main_layout.addWidget(self.robtarget_input)
        
        # Add label for converted robtargets
        output_label = QLabel("CONVERTED ROBTARGETS")
        output_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(output_label)
        
        self.result_list = QListWidget()
        set_output_text_style(self.result_list)
        main_layout.addWidget(self.result_list)
        
        convert_copy_layout = QHBoxLayout()
        
        convert_button = QPushButton("Convert")
        set_button_style(convert_button)
        convert_button.clicked.connect(self.convert_targets)
        convert_copy_layout.addWidget(convert_button)
        
        copy_button = QPushButton("Copy Results")
        set_button_style(copy_button)
        copy_button.clicked.connect(self.copy_results)
        convert_copy_layout.addWidget(copy_button)
        
        main_layout.addLayout(convert_copy_layout)
        
        self.apply_theme()

    def show_input_window(self):
        input_window = InputWindow(self)
        input_window.inputUpdated.connect(self.update_input)
        input_window.set_theme(self.current_theme == 'dark')
        input_window.setWindowModality(Qt.ApplicationModal)
        input_window.show()

    def show_coordinate_system_window(self):
        coord_system_window = CoordinateSystemInputWindow(self)
        coord_system_window.coordinateSystemsAdded.connect(self.add_coordinate_systems)
        coord_system_window.set_theme(self.current_theme == 'dark')
        coord_system_window.setWindowModality(Qt.ApplicationModal)
        coord_system_window.show()

    def set_theme(self, theme):
        self.current_theme = theme
        self.apply_theme()

    def apply_theme(self):
        if self.current_theme == 'dark':
            # Apply dark theme styles
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: #ffffff; }
                QLineEdit, QComboBox { 
                    background-color: #3a3a3a; 
                    color: #ffffff; 
                    border: 1px solid #ffffff;
                }
                QPushButton { 
                    background-color: #3a3a3a; 
                    color: #ffffff; 
                    border: 1px solid #ffffff;
                }
                QPushButton:hover { background-color: #4a4a4a; }
            """)
        else:
            # Apply light theme styles
            self.setStyleSheet("""
                QWidget { background-color: #ffffff; color: #000000; }
                QLineEdit, QComboBox { 
                    background-color: #f0f0f0; 
                    color: #000000; 
                    border: 1px solid #000000;
                }
                QPushButton { 
                    background-color: #f0f0f0; 
                    color: #000000; 
                    border: 1px solid #000000;
                }
                QPushButton:hover { background-color: #e0e0e0; }
            """)

    def get_robtarget_data(self, target_name):
        """Retrieve full robtarget data for a given target name."""
        data = self.robtarget_data.get(target_name)
        #print(f"Retrieved data for {target_name}: {data}")  # Debug print
        return data

    def add_coordinate_systems(self, coord_systems):
        """Adds new coordinate systems to the application."""
        for name, params in coord_systems.items():
            if name not in self.coordinate_systems:
                self.coordinate_systems[name] = params
                self.input_cs_combo.addItem(name)
                self.output_cs_combo.addItem(name)
            else:
                print(f"Coordinate system '{name}' already exists.")

    def update_input(self, input_text):
        #print("Updating input in TargetConverterApp with:", input_text)  # Debug print
        self.robtarget_input.clear()
        self.robtarget_data.clear()  # Clear previous data
        for line in input_text.split('\n'):
            line = line.strip()  # Strip whitespace
            match = re.match(r'(local\s+)?(const\s+)?robtarget\s+(\w+)\s*:=\s*(\[\[[-\d.,]+\],\[[-\d.,]+\],\[[-\d.,]+\],\[[-\d.E+,]+\]\]);', line, re.IGNORECASE)
            if match:
                scope = []
                if match.group(1):
                    scope.append('LOCAL')
                if match.group(2):
                    scope.append('CONST')
                scope = ' '.join(scope)
                target_name = match.group(3)
                target_data = match.group(4)
                #print(f"Adding target to list: {target_name}")  # Debug print
                self.robtarget_input.addItem(target_name)
                self.robtarget_data[target_name] = {
                    'scope': scope,
                    'data': self.parse_robtarget_data(target_data)
                }
            else:
                print(f"No match for line: {line}")  # Debug print
        #print(f"Total items in robtarget_input: {self.robtarget_input.count()}")  # Debug print

    def parse_robtarget_data(self, data_string):
        """Parse the robtarget data string into a list of lists."""
        parts = data_string.strip('[]').split('],[')
        return [
            [float(x) for x in parts[0].split(',')],  # position
            [float(x) for x in parts[1].split(',')],  # orientation
            [int(x) for x in parts[2].split(',')],    # robot_config
            [float(x) for x in parts[3].split(',')]   # external_axis
        ]
    
    def convert_targets(self):
        input_cs = self.input_cs_combo.currentText()
        output_cs = self.output_cs_combo.currentText()
        if input_cs == output_cs:
            print("Input and output coordinate systems must be different.")
            return

        self.result_list.clear()
        self.converted_data.clear()
        results = []
        errors = []
        
        for i in range(self.robtarget_input.count()):
            target_name = self.robtarget_input.item(i).text()
            robtarget_info = self.get_robtarget_data(target_name)
            if robtarget_info:
                try:
                    transformed_target = transform_robtarget(
                        robtarget_info['data'], self.coordinate_systems[output_cs], self.coordinate_systems[input_cs]
                    )
                    self.converted_data[target_name] = {
                        'scope': robtarget_info['scope'],
                        'data': transformed_target
                    }
                    results.append(f"{target_name}")
                except Exception as e:
                    error_msg = f"Error processing target: {target_name}"
                    results.append(error_msg)
                    errors.append(error_msg)
            else:
                results.append(f"Invalid target: {target_name}")
        
        if results:
            self.result_list.addItems(results)
        else:
            self.result_list.addItem("No valid robtargets were found.")
            
        if errors:
            print("Errors encountered during conversion:\n", "\n".join(errors))

    def copy_results(self):
        full_results = []
        for target_name, converted_info in self.converted_data.items():
            scope = converted_info['scope']
            formatted_data = format_robtarget(converted_info['data'])
            if scope:
                full_results.append(f"{scope} robtarget {target_name}:={formatted_data};")
            else:
                full_results.append(f"robtarget {target_name}:={formatted_data};")
        
        if full_results:
            results_text = "\n".join(full_results)
            pyperclip.copy(results_text)
            print("Full results copied to clipboard.")
        else:
            print("No results to copy.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    main_app = TargetConverterApp()
    main_app.show()
    
    sys.exit(app.exec_())