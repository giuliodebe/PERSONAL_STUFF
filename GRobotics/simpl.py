import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog

class SimplifiedRobotParser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Simplified Robot Parser')
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.select_file_button = QPushButton('Select File', self)
        self.select_file_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_file_button)

        self.parse_button = QPushButton('Parse File', self)
        self.parse_button.clicked.connect(self.parse_file)
        layout.addWidget(self.parse_button)

        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.file_path = None

    def select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Text File", "", "Text Files (*.mod);;All Files (*)", options=options)
        if file_name:
            self.file_path = file_name
            self.output_text.setText(f"Selected file: {self.file_path}")

    def parse_file(self):
        if not self.file_path:
            self.output_text.setText("Please select a file first.")
            return

        try:
            with open(self.file_path, 'r') as file:
                content = file.read()
            self.output_text.setText(f"File content:\n{content}")
        except Exception as e:
            self.output_text.setText(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SimplifiedRobotParser()
    ex.show()
    sys.exit(app.exec_())