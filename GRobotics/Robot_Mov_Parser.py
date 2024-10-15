import sys
import os
import re
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
                             QFileDialog, QMessageBox, QRadioButton, QButtonGroup, QLabel, QLineEdit, QListWidget)
from PyQt5.QtCore import Qt

from GUI_settings import (set_dark_theme, set_light_theme, set_button_style, set_title_font,
                          set_common_stylesheet, set_input_field_style, set_output_text_style)

class RobotMovementParser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'  # Initialize the current_theme attribute
        self.initUI()
        self.variable_counter = 10
        self.generated_variables = []
        self.coordinate_to_variable = {}
        self.file_path = None

    def initUI(self):
        self.setWindowTitle('Robot Movement Parser')
        width = 800
        height = 600
        self.setGeometry(100, 100, width, height)
        max_width = int(width * 1.2)
        max_height = int(height * 1.2)
        min_width = int(width * 0.8)
        min_height = int(height * 0.8)
        self.setMaximumSize(max_width, max_height)
        self.setMinimumSize(min_width, min_height)


        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("Robot Movement Parser")
        set_title_font(title_label)
        main_layout.addWidget(title_label)

        # File selection button
        self.select_file_button = QPushButton('Select File', self)
        self.select_file_button.clicked.connect(self.select_file)
        main_layout.addWidget(self.select_file_button)

        # Format selection
        format_layout = QHBoxLayout()
        
        # Scope selection
        scope_group = QButtonGroup(self)
        self.scope_global = QRadioButton("GLOBAL")
        self.scope_local = QRadioButton("LOCAL")
        scope_group.addButton(self.scope_global)
        scope_group.addButton(self.scope_local)
        self.scope_global.setChecked(True)
        format_layout.addWidget(QLabel("Scope:"))
        format_layout.addWidget(self.scope_global)
        format_layout.addWidget(self.scope_local)

        # Type selection
        type_group = QButtonGroup(self)
        self.type_const = QRadioButton("CONST")
        self.type_var = QRadioButton("VAR")
        type_group.addButton(self.type_const)
        type_group.addButton(self.type_var)
        self.type_const.setChecked(True)
        format_layout.addWidget(QLabel("Type:"))
        format_layout.addWidget(self.type_const)
        format_layout.addWidget(self.type_var)

        # Variable name base
        format_layout.addWidget(QLabel("Variable base name:"))
        self.var_base_name = QLineEdit("p_")
        format_layout.addWidget(self.var_base_name)

        main_layout.addLayout(format_layout)

        # Parse button
        self.parse_button = QPushButton('Parse Movements', self)
        self.parse_button.clicked.connect(self.parse_movements)
        main_layout.addWidget(self.parse_button)

        # Save file button
        self.save_file_button = QPushButton('Save File', self)
        self.save_file_button.clicked.connect(self.save_file)
        main_layout.addWidget(self.save_file_button)

        # Modify file button
        self.modify_file_button = QPushButton('Modify File', self)
        self.modify_file_button.clicked.connect(self.modify_file)
        main_layout.addWidget(self.modify_file_button)

        # Output text area
        self.output_text = QListWidget(self)
        main_layout.addWidget(self.output_text)

        # Change the label to indicate input directory
        self.input_dir_label = QLabel('Input Directory: Not selected', self)
        main_layout.addWidget(self.input_dir_label)
       
        self.apply_theme()

    def apply_theme(self):
        is_dark = self.current_theme == 'dark'
        if is_dark:
            set_dark_theme(self)
            self.setStyleSheet(set_common_stylesheet('dark'))
            label_style = "QLabel { color: #ffffff; }"
        else:
            set_light_theme(self)
            self.setStyleSheet(set_common_stylesheet('light'))
            label_style = "QLabel { color: #000000; }"
        
        # Apply theme to buttons
        for button in self.findChildren(QPushButton):
            set_button_style(button, self.current_theme)
        
        # Apply theme to input fields
        set_input_field_style(self.var_base_name, self.current_theme)
        
        # Apply theme to output text
        set_output_text_style(self.output_text, self.current_theme)
        
        # Apply theme to labels
        for label in self.findChildren(QLabel):
            label.setStyleSheet(label_style)

    def set_theme(self, theme):
        self.current_theme = theme
        self.apply_theme()

    def select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Text File", "", "Text Files (*.mod);;All Files (*)", options=options)
        if file_name:
            self.file_path = file_name
            self.output_text.addItem(f"Selected file: {self.file_path}")
            # Update the input directory label
            input_dir = os.path.dirname(self.file_path)
            self.input_dir_label.setText(f'Input Directory: {input_dir}')

    def parse_movements(self):
        if not self.file_path:
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return

        try:
            lines = self.read_file(self.file_path)
            move_instructions = self.identify_move_instructions(lines)
            self.generated_variables = []
            self.variable_counter = 10
            self.coordinate_to_variable = {}

            for instruction in move_instructions:
                coordinates = self.extract_coordinates(instruction)
                if coordinates:
                    variable = self.generate_variable(coordinates)
                    if variable:  # Only add if a new variable was generated
                        self.generated_variables.append(variable)

            self.output_text.clear()
            self.output_text.addItems(self.generated_variables)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def read_file(self, file_path):
        """Read the contents of the file."""
        with open(file_path, 'r') as file:
            return file.readlines()

    def identify_move_instructions(self, lines):
        """Identify move instructions in the robotic program."""
        move_instructions = []
        move_pattern = re.compile(r'\b(MoveJ|MoveL|MoveC)\b', re.IGNORECASE)
        for line in lines:
            if move_pattern.search(line):
                move_instructions.append(line.strip())
        return move_instructions

    def extract_coordinates(self, move_instruction):
        """Extract full coordinate sequence from a move instruction."""
        coord_pattern = re.compile(r'\[(\[[-+]?\d+\.?\d*,[-+]?\d+\.?\d*,[-+]?\d+\.?\d*\],\[[-+]?\d+\.?\d*,[-+]?\d+\.?\d*,[-+]?\d+\.?\d*,[-+]?\d+\.?\d*\],\[[-+]?\d+,[-+]?\d+,[-+]?\d+,[-+]?\d+\],\[(?:9E\+09,){5}9E\+09\])\]')
        match = coord_pattern.search(move_instruction)
        if match:
            return match.group(1)
        return None

    def generate_variable(self, coordinates):
        """Generate a new variable with coordinates based on selected format."""
        # Check if coordinates already have a variable assigned
        if coordinates in self.coordinate_to_variable:
            return None  # Skip generation if already exists

        scope = "LOCAL " if self.scope_local.isChecked() else ""
        var_type = "CONST" if self.type_const.isChecked() else "VAR"
        base_name = self.var_base_name.text() or "p_"
        variable_name = f"{base_name}{self.variable_counter}"
        self.variable_counter += 10
        
        # Store the new variable in the coordinate_to_variable dictionary
        self.coordinate_to_variable[coordinates] = variable_name
        
        return f"{scope}{var_type} Robtarget {variable_name} := [{coordinates}];"
   
    def save_file(self):
        if not self.generated_variables:
            QMessageBox.warning(self, "Warning", "No variables generated. Please parse movements first.")
            return

        default_dir = os.path.dirname(self.file_path) if self.file_path else ""
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_dir, "MOD Files (*.mod)")

        if save_path:
            try:
                with open(save_path, 'w') as file:
                    file.write("\n".join(self.generated_variables))
                QMessageBox.information(self, "Success", f"File saved successfully: {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while saving the file: {str(e)}")

    def modify_file(self):
        if not self.generated_variables:
            QMessageBox.warning(self, "Warning", "No variables generated. Please parse movements first.")
            return

        if not self.file_path:
            QMessageBox.warning(self, "Warning", "No source file selected.")
            return

        default_dir = os.path.dirname(self.file_path)
        default_name = f"modified_{os.path.basename(self.file_path)}"
        new_file_path, _ = QFileDialog.getSaveFileName(self, "Save Modified File", os.path.join(default_dir, default_name), "MOD Files (*.mod)")

        if new_file_path:
            try:
                # Create a copy of the original file
                shutil.copy2(self.file_path, new_file_path)

                # Read the contents of the new file
                with open(new_file_path, 'r') as file:
                    lines = file.readlines()

                # Find the line starting with "MODULE" and insert the new variables after it
                module_line_index = next((i for i, line in enumerate(lines) if line.strip().startswith("MODULE")), -1)
                if module_line_index != -1:
                    lines.insert(module_line_index + 1, "\n" + "\n".join(self.generated_variables) + "\n")
                else:
                    lines.insert(0, "\n".join(self.generated_variables) + "\n")

                # Replace coordinates with variable names in move instructions
                for i, line in enumerate(lines):
                    if any(move in line.upper() for move in ["MOVEJ", "MOVEL", "MOVEC"]):
                        for coords, var_name in self.coordinate_to_variable.items():
                            if coords in line:
                                # Extract only the variable name without scope, type, and robtarget
                                var_name_only = var_name.split()[-1]
                                lines[i] = line.replace(f"[{coords}]", var_name_only)

                # Write the modified contents back to the file
                with open(new_file_path, 'w') as file:
                    file.writelines(lines)

                QMessageBox.information(self, "Success", f"File modified successfully: {new_file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while modifying the file: {str(e)}")

    # ... (keep the rest of the methods as they are) ...

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RobotMovementParser()
    ex.show()
    sys.exit(app.exec_())
