import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFormLayout,
                             QDialog, QDialogButtonBox, QListWidget, QComboBox, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPalette, QColor,QTextCharFormat
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
from scipy.spatial.transform import Rotation
import pyperclip
import re

def transform_robtarget(robtarget, input_coord_system, output_coord_system):
    # Extract components from robtarget
    position = np.array(robtarget[0])
    orientation = np.array(robtarget[1])
    robot_config = robtarget[2]
    external_axis = robtarget[3]

    # Extract components from coordinate systems
    input_position = np.array(input_coord_system[0])
    input_orientation = Rotation.from_quat(input_coord_system[1])
    output_position = np.array(output_coord_system[0])
    output_orientation = Rotation.from_quat(output_coord_system[1])

    # Transform position
    # Move from input system to world coordinates
    world_position = input_orientation.apply(position) + input_position
    # Then, move from world coordinates to output system
    transformed_position = output_orientation.inv().apply(world_position - output_position)

    # Transform orientation
    # Combine rotations: output_rotation^-1 * input_rotation * target_rotation
    target_rotation = Rotation.from_quat(orientation)
    transformed_rotation = output_orientation.inv() * input_orientation * target_rotation
    transformed_orientation = transformed_rotation.as_quat()

    # Construct transformed robtarget
    transformed_robtarget = [
        transformed_position.tolist(),
        transformed_orientation.tolist(),
        robot_config,
        external_axis
    ]

    return transformed_robtarget

def format_robtarget(robtarget):
    position = [f"{x:.2f}" for x in robtarget[0]]
    orientation = [f"{x:.6f}" for x in robtarget[1]]
    robot_config = [str(int(x)) for x in robtarget[2]]
    external_axis = [f"{x:.2f}" if abs(x - 9e9) >= 1e-6 else "9E+09" for x in robtarget[3]]
    
    return (f"[[{', '.join(position)}], [{', '.join(orientation)}], "
            f"[{', '.join(robot_config)}], [{', '.join(external_axis)}]]")

class CoordinateSystemInputWindow(QWidget):
    coordinateSystemsAdded = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Coordinate Systems")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter coordinate systems (one per line) in the format:\nTASK PERS wobjdata Name :=[FALSE,TRUE,"",[[x,y,z],[qw,qx,qy,qz]],[[0,0,0],[1,0,0,0]]];")
        layout.addWidget(self.text_edit)
        
        add_button = QPushButton("Apply")
        add_button.clicked.connect(self.add_coordinate_systems)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(add_button)
        
        self.setLayout(layout)
 
    def add_coordinate_systems(self):
        input_text = self.text_edit.toPlainText().strip()
        coord_systems = {}
        for line in input_text.split('\n'):
            match = re.match(r'TASK\s+PERS\s+wobjdata\s+(\w+)\s*:=\s*\[.*?\[\[([-\d.]+),([-\d.]+),([-\d.]+)\],\[([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)\]\]', line.strip())
            if match:
                name = match.group(1)
                position = [float(match.group(2)), float(match.group(3)), float(match.group(4))]
                orientation = [float(match.group(5)), float(match.group(6)), float(match.group(7)), float(match.group(8))]
                coord_systems[name] = {'position': position, 'orientation': orientation}
                print(f"Parsed coordinate system: {name} - Position: {position}, Orientation: {orientation}")
        
        if coord_systems:
            self.coordinateSystemsAdded.emit(coord_systems)
            self.text_edit.clear()
        else:
            print("No valid coordinate systems found. Please check the format and try again.")
        self.close()

class InputWindow(QWidget):
    inputUpdated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input Multiple Targets")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                color: black;
                background-color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        self.text_edit.setPlaceholderText("Enter targets here (one per line)\nFormat: SCOPE robtarget TargetName := [x,y,z],[qw,qx,qy,qz],[cfg1,cfg2,cfg3,cfg4],[ext1,ext2,ext3,ext4,ext5,ext6];")
        layout.addWidget(self.text_edit)
        
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_input)
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(apply_button)
        
        self.setLayout(layout)

    def apply_input(self):
        self.inputUpdated.emit(self.text_edit.toPlainText())
        self.close()

class TargetConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Target Converter")
        self.setGeometry(100, 100, 1000, 600)
        
        self.input_window = InputWindow()
        self.input_window.inputUpdated.connect(self.update_input)
        self.coordinate_systems = {
        'Wobj0': {'position': [0, 0, 0], 'orientation': [1, 0, 0, 0]}
        }
        self.coord_system_window = CoordinateSystemInputWindow()
        self.coord_system_window.coordinateSystemsAdded.connect(self.add_coordinate_systems)
        
        self.coordinate_systems = {
            'Wobj0': {'position': [0, 0, 0], 'orientation': [1, 0, 0, 0]}
        }
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Left panel for target names preview
        left_panel = self.create_group_box("TARGET NAMES")
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        self.target_list = QListWidget()
        self.target_list.setStyleSheet("""
            QListWidget {
                color: black;
                background-color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        left_layout.addWidget(self.target_list)
        
        # Button to toggle input window
        self.input_button = QPushButton("ADD TARGETS")
        self.input_button.clicked.connect(self.toggle_input_window)
        self.input_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        left_layout.addWidget(self.input_button)
        
        # Panel for coordinate systems
        coord_panel = self.create_group_box("COORDINATE SYSTEMS")
        coord_layout = QVBoxLayout()
        coord_panel.setLayout(coord_layout)
        
        self.coord_list = QListWidget()
        self.coord_list.setStyleSheet("""
            QListWidget {
                color: black;
                background-color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        self.coord_list.addItem("Wobj0")
        coord_layout.addWidget(self.coord_list)
        
        add_coord_system_button = QPushButton("ADD COORD SYSTEM")
        add_coord_system_button.clicked.connect(self.toggle_coord_system_window)
        add_coord_system_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        coord_layout.addWidget(add_coord_system_button)
        
        # Central panel for INPUT, OUTPUT, and CONVERT
        central_panel = QWidget()
        central_layout = QVBoxLayout()
        central_panel.setLayout(central_layout)
        
        # Add top spacer
        central_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Input coordinate system selection
        input_group = self.create_group_box("INPUT")
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)
        self.input_coord_system_combo = QComboBox()
        self.input_coord_system_combo.addItem("Wobj0")
        self.input_coord_system_combo.setCurrentIndex(0)  # Set Wobj0 as default
        input_layout.addWidget(self.input_coord_system_combo)
        central_layout.addWidget(input_group)
        
        # Output coordinate system selection
        output_group = self.create_group_box("OUTPUT")
        output_layout = QVBoxLayout()
        output_group.setLayout(output_layout)
        self.output_coord_system_combo = QComboBox()
        self.output_coord_system_combo.addItem("Wobj0")
        self.output_coord_system_combo.setCurrentIndex(0)  # Set Wobj0 as default
        output_layout.addWidget(self.output_coord_system_combo)
        central_layout.addWidget(output_group)
        
        # Convert button
        convert_button = QPushButton("CONVERT")
        convert_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        convert_button.clicked.connect(self.convert_targets)
        central_layout.addWidget(convert_button)
        
        # Add bottom spacer
        central_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
         # Result display
        result_panel = self.create_group_box("CONVERTED TARGETS")
        result_layout = QVBoxLayout()
        result_panel.setLayout(result_layout)
        
        self.result_list = QListWidget()
        self.result_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: red;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        result_layout.addWidget(self.result_list)

        # Copy to Clipboard button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        result_layout.addWidget(copy_button)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(coord_panel, 2)
        main_layout.addWidget(central_panel, 2)
        main_layout.addWidget(result_panel, 3)
        
        # Set dark theme
        self.set_dark_theme()
        
        # Store the full input text
        self.full_input_text = ""
    
        self.converted_targets = []  # Store full converted target information

    def toggle_input_window(self):
        if self.input_window.isVisible():
            self.input_window.hide()
        else:
            self.input_window.show()
    
    def toggle_coord_system_window(self):
        if self.coord_system_window.isVisible():
            self.coord_system_window.hide()
        else:
            self.coord_system_window.show()
    
    def update_input(self, full_text):
        self.full_input_text = full_text
        self.target_list.clear()
        target_names = self.extract_target_names(full_text)
        self.target_list.addItems(target_names)
    
    def extract_target_names(self, full_text):
        target_names = []
        for line in full_text.split('\n'):
            match = re.match(r'\w+\s+robtarget\s+(\w+)\s*:=', line.strip())
            if match:
                target_names.append(match.group(1))
        return target_names
    
    def add_coordinate_systems(self, new_coord_systems):
        for name, coord_system in new_coord_systems.items():
            position = coord_system['position']
            orientation = coord_system['orientation']
            self.coordinate_systems[name] = {'position': position, 'orientation': orientation}
            if self.coord_list.findItems(name, Qt.MatchExactly) == []:
                self.coord_list.addItem(name)
            if self.input_coord_system_combo.findText(name) == -1:
                self.input_coord_system_combo.addItem(name)
            if self.output_coord_system_combo.findText(name) == -1:
                self.output_coord_system_combo.addItem(name)
    
            print(f"Updated coordinate systems: {self.coordinate_systems}")

    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        self.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    def create_group_box(self, title):
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """)
        return group_box
    
    def convert_targets(self):
        input_targets = self.full_input_text.strip().split('\n')
        input_coord_system_name = self.input_coord_system_combo.currentText()
        output_coord_system_name = self.output_coord_system_combo.currentText()
        
        input_coord_system = self.coordinate_systems.get(input_coord_system_name)
        output_coord_system = self.coordinate_systems.get(output_coord_system_name)
        
        if not input_coord_system or not output_coord_system:
            print(f"Error: Invalid coordinate system selected.")
            return

        self.converted_targets = [f"! Converted from {input_coord_system_name} to {output_coord_system_name}"]
        converted_names = []
        for target in input_targets:
            try:
                # Parse the input target
                match = re.match(r'(\w+)\s+robtarget\s+(\w+)\s*:=\s*(\[.*\])\s*;', target)
                if not match:
                    raise ValueError(f"Invalid target format: {target}")
                
                scope, name, robtarget_str = match.groups()
                
                # Parse the robtarget components
                components = re.findall(r'\[([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?(?:,[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)*)\]', robtarget_str)
                if len(components) != 4:
                    raise ValueError(f"Invalid robtarget format: {robtarget_str}")
                
                position = list(map(float, components[0].split(',')))
                orientation = list(map(float, components[1].split(',')))
                robot_config = list(map(int, components[2].split(',')))
                external_axis = [float(x) if x.upper() != "9E+09" else 9e9 for x in components[3].split(',')]
                
                robtarget = [position, orientation, robot_config, external_axis]
                
                # Transform from input to output coordinate system
                final_target = transform_robtarget(robtarget, 
                                                [input_coord_system['position'], input_coord_system['orientation']], 
                                                [output_coord_system['position'], output_coord_system['orientation']])
                
                # Format the final target for display
                formatted_target = format_robtarget(final_target)
                self.converted_targets.append(f"{scope} robtarget {name} := {formatted_target};")
                converted_names.append(name)
                
                # Debug print statements
                print(f"\nProcessing target: {name}")
                print(f"Input coordinate system: {input_coord_system}")
                print(f"Output coordinate system: {output_coord_system}")
                print(f"Original target position: {position}")
                print(f"Original target orientation: {orientation}")

                final_target = transform_robtarget(robtarget, 
                                                [input_coord_system['position'], input_coord_system['orientation']], 
                                                [output_coord_system['position'], output_coord_system['orientation']])

                print(f"Transformed target position: {final_target[0]}")
                print(f"Transformed target orientation: {final_target[1]}")
                print(f"Difference in position: {np.array(final_target[0]) - np.array(position)}")

            except Exception as e:
                print(f"Error processing target: {target}\nError: {str(e)}")
                # Add the original target to the list if there's an error
                self.converted_targets.append(f"! Error: {target}")
        
        self.display_results(converted_names)
    def copy_to_clipboard(self):
        clipboard_content = "\n".join(self.converted_targets)
        pyperclip.copy(clipboard_content)

    def display_results(self, converted_names):
        self.result_list.clear()
        for target in self.converted_targets:
            if target.startswith('!'):
                self.result_list.addItem(target)
            else:
                name = re.search(r'robtarget\s+(\w+)', target)
                if name:
                    self.result_list.addItem(name.group(1))
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TargetConverterApp()
    window.show()
    sys.exit(app.exec_())  