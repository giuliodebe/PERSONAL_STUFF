import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFormLayout,
                             QDialog, QDialogButtonBox, QListWidget)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
from scipy.spatial.transform import Rotation
import re

def transform_robtarget(robtarget, coord_system):
    # Extract components from robtarget
    position = np.array(robtarget[0])
    orientation = np.array(robtarget[1])
    robot_config = robtarget[2]
    external_axis = robtarget[3]

    # Extract components from coord_system
    coord_position = np.array(coord_system[0])
    coord_orientation = np.array(coord_system[1])

    # Create rotation matrix from quaternion
    rotation = Rotation.from_quat(coord_orientation)
    rotation_matrix = rotation.as_matrix()

    # Transform position
    transformed_position = np.dot(rotation_matrix, position) + coord_position

    # Transform orientation
    coord_rotation = Rotation.from_quat(coord_orientation)
    target_rotation = Rotation.from_quat(orientation)
    transformed_rotation = coord_rotation * target_rotation
    transformed_orientation = transformed_rotation.as_quat()

    # Handle external axis
    transformed_external_axis = []
    for value in external_axis:
        if isinstance(value, str) and value.upper() == "9E+09":
            transformed_external_axis.append(9e9)
        elif isinstance(value, (int, float)) and abs(value - 9e9) < 1e-6:
            transformed_external_axis.append(9e9)
        else:
            transformed_external_axis.append(value)

    # Construct transformed robtarget
    transformed_robtarget = [
        transformed_position.tolist(),
        transformed_orientation.tolist(),
        robot_config,
        transformed_external_axis
    ]

    return transformed_robtarget

def format_robtarget(robtarget):
    position = [f"{x:.2f}" for x in robtarget[0]]
    orientation = [f"{x:.6f}" for x in robtarget[1]]
    robot_config = [str(int(x)) for x in robtarget[2]]
    external_axis = [f"{x:.2f}" if abs(x - 9e9) >= 1e-6 else "9E+09" for x in robtarget[3]]
    
    return (f"[[{', '.join(position)}], [{', '.join(orientation)}], "
            f"[{', '.join(robot_config)}], [{', '.join(external_axis)}]]")

class InputWindow(QWidget):
    inputUpdated = pyqtSignal(str, list)

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
        input_text = self.text_edit.toPlainText()
        target_names = self.extract_target_names(input_text)
        self.inputUpdated.emit(input_text, target_names)
    
    def extract_target_names(self, input_text):
        target_names = []
        for line in input_text.split('\n'):
            match = re.match(r'\w+\s+robtarget\s+(\w+)\s*:=', line.strip())
            if match:
                target_names.append(match.group(1))
        return target_names
    
class MultiTargetInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_targets(self):
        return self.text_edit.toPlainText()

class TargetConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Target Converter")
        self.setGeometry(100, 100, 800, 600)
        
        self.input_window = InputWindow()
        self.input_window.inputUpdated.connect(self.update_input)
        
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
        self.input_button = QPushButton("INPUT MULTIPLE TARGETS")
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

        # Middle panel for original coordinate system
        middle_panel = self.create_group_box("ORIGINAL COORDINATE SYSTEM")
        middle_layout = QFormLayout()
        middle_panel.setLayout(middle_layout)
        
        self.orig_x = QLineEdit("0")
        self.orig_y = QLineEdit("0")
        self.orig_z = QLineEdit("0")
        self.orig_qw = QLineEdit("1")
        self.orig_qx = QLineEdit("0")
        self.orig_qy = QLineEdit("0")
        self.orig_qz = QLineEdit("0")
        
        self.add_form_row(middle_layout, "X:", self.orig_x)
        self.add_form_row(middle_layout, "Y:", self.orig_y)
        self.add_form_row(middle_layout, "Z:", self.orig_z)
        self.add_form_row(middle_layout, "QW:", self.orig_qw)
        self.add_form_row(middle_layout, "QX:", self.orig_qx)
        self.add_form_row(middle_layout, "QY:", self.orig_qy)
        self.add_form_row(middle_layout, "QZ:", self.orig_qz)
        
        # Right panel for target coordinate system
        right_panel = self.create_group_box("TARGET COORDINATE SYSTEM")
        right_layout = QFormLayout()
        right_panel.setLayout(right_layout)
        
        self.target_x = QLineEdit("0")
        self.target_y = QLineEdit("0")
        self.target_z = QLineEdit("0")
        self.target_qw = QLineEdit("1")
        self.target_qx = QLineEdit("0")
        self.target_qy = QLineEdit("0")
        self.target_qz = QLineEdit("0")
        
        self.add_form_row(right_layout, "X:", self.target_x)
        self.add_form_row(right_layout, "Y:", self.target_y)
        self.add_form_row(right_layout, "Z:", self.target_z)
        self.add_form_row(right_layout, "QW:", self.target_qw)
        self.add_form_row(right_layout, "QX:", self.target_qx)
        self.add_form_row(right_layout, "QY:", self.target_qy)
        self.add_form_row(right_layout, "QZ:", self.target_qz)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel)
        main_layout.addWidget(right_panel)
        
        # Convert button with updated style
        convert_button = QPushButton("CONVERT")
        convert_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: black;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        convert_button.clicked.connect(self.convert_targets)
        main_layout.addWidget(convert_button)
        
        # Result display
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("""
            QTextEdit {
                color: white;
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        main_layout.addWidget(self.result_display)
        
        # Set dark theme
        self.set_dark_theme()
        # Store the full input text
        self.full_input_text = ""

    def toggle_input_window(self):
        if self.input_window.isVisible():
            self.input_window.hide()
        else:
            self.input_window.show()

    def update_input(self, full_text, target_names):
        self.full_input_text = full_text
        self.target_list.clear()
        self.target_list.addItems(target_names)

    def create_group_box(self, title):
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                background-color: #2b2b2b;
            }
        """)
        return group_box
    
    def add_form_row(self, layout, label_text, input_widget):
        label = QLabel(label_text.upper())
        label.setStyleSheet("color: white; font-weight: bold;")
        input_widget.setStyleSheet("""
            QLineEdit {
                color: black;
                background-color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        layout.addRow(label, input_widget)
    
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
    
    def open_multi_target_dialog(self):
        dialog = MultiTargetInputDialog(self)
        if dialog.exec_():
            targets = dialog.get_targets()
            self.target_input.setPlainText(targets)

    def convert_targets(self):
        input_targets = self.full_input_text.strip().split('\n')
          
        orig_coord_system = [
            [float(self.orig_x.text()), float(self.orig_y.text()), float(self.orig_z.text())],
            [float(self.orig_qw.text()), float(self.orig_qx.text()), float(self.orig_qy.text()), float(self.orig_qz.text())]
        ]
        
        target_coord_system = [
            [float(self.target_x.text()), float(self.target_y.text()), float(self.target_z.text())],
            [float(self.target_qw.text()), float(self.target_qx.text()), float(self.target_qy.text()), float(self.target_qz.text())]
        ]
        
        results = []
        for target in input_targets:
            try:
                # Strip whitespace from the entire target string
                target = target.strip()
                
                # Parse the input target
                match = re.match(r'(\w+)\s+robtarget\s+(\w+)\s*:=\s*(\[.*\]);', target)
                if not match:
                    raise ValueError(f"Invalid target format: {target}")
                
                scope, name, robtarget_str = match.groups()
                
                # Remove all whitespace from the robtarget string
                robtarget_str = re.sub(r'\s+', '', robtarget_str)
                
                parts = robtarget_str.split('],[')
                position = list(map(float, parts[0].strip('[]').split(',')))
                orientation = list(map(float, parts[1].strip('[]').split(',')))
                robot_config = list(map(float, parts[2].strip('[]').split(',')))
                external_axis = parts[3].strip('[]').split(',')
                
                # Convert external_axis values to float, except for "9E+09"
                external_axis = [float(x) if x.upper() != "9E+09" else 9e9 for x in external_axis]
                
                robtarget = [position, orientation, robot_config, external_axis]
                
                # Transform from original to base coordinate system
                base_target = transform_robtarget(robtarget, orig_coord_system)
                
                # Transform from base to target coordinate system
                final_target = transform_robtarget(base_target, target_coord_system)
                
                # Format the final target for display
                formatted_target = format_robtarget(final_target)
                results.append(f"{scope} robtarget {name} := {formatted_target};")
            except Exception as e:
                results.append(f"Error processing target: {target}\nError: {str(e)}")
        
        self.result_display.setPlainText('\n\n'.join(results))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TargetConverterApp()
    window.show()
    sys.exit(app.exec_())