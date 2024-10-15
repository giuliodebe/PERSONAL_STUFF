from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt

# Existing dark theme function
def set_dark_theme(widget):
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
    widget.setPalette(dark_palette)

# New light theme function
def set_light_theme(widget):
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, Qt.black)
    light_palette.setColor(QPalette.Base, Qt.white)
    light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    light_palette.setColor(QPalette.ToolTipBase, Qt.white)
    light_palette.setColor(QPalette.ToolTipText, Qt.black)
    light_palette.setColor(QPalette.Text, Qt.black)
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ButtonText, Qt.black)
    light_palette.setColor(QPalette.BrightText, Qt.red)
    light_palette.setColor(QPalette.Link, QColor(0, 0, 255))
    light_palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    light_palette.setColor(QPalette.HighlightedText, Qt.white)
    widget.setPalette(light_palette)

# Update the existing function to support both themes
def set_button_style(widget, theme='dark'):
    if theme == 'dark':
        base_color = "#1565c0"
        hover_color = "#1976d2"
        text_color = "white"
    else:
        base_color = "#2196f3"
        hover_color = "#42a5f5"
        text_color = "white"

    widget.setStyleSheet(f"""
        QPushButton {{
            background-color: {base_color};
            color: {text_color};
            font-weight: bold;
            font-size: 12px;
            padding: 5px 8px;
            border: none;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
    """)

    # Adjust button size based on content
    size_hint = widget.sizeHint()
    widget.setMinimumSize(size_hint.width() + 10, size_hint.height() + 5)  # Reduced padding

# Updated to accept a label for font styling
def set_title_font(label):
    label.setFont(QFont("Arial", 18, QFont.Bold))

def set_tab_widget_style(widget, theme='dark'):
    if theme == 'dark':
        widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #1e1e1e;
                color: #ffffff;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: #3b3b3b;
            }
        """)
    else:
        widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: #f0f0f0;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #000000;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
            }
        """)

def set_input_field_style(widget, theme='dark'):
    if theme == 'dark':
        widget.setStyleSheet("""
            QLineEdit, QComboBox {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                color: white;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow_white.png);
                width: 12px;
                height: 12px;
            }
        """)
    else:
        widget.setStyleSheet("""
            QLineEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                color: black;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow_black.png);
                width: 12px;
                height: 12px;
            }
        """)

# New function to set common stylesheet for both themes
def set_common_stylesheet(theme='dark'):
    if theme == 'dark':
        return """
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QLineEdit, QTextEdit { background-color: #3b3b3b; border: 1px solid #555555; }
            QPushButton { background-color: #1565c0; padding: 5px; }
            QPushButton:hover { background-color: #1976d2; }
            QComboBox { background-color: #3b3b3b; border: 1px solid #555555; padding: 5px; }
            QTabBar::tab { background-color: #1e1e1e; color: #ffffff; }
            QTabBar::tab:selected { background-color: #3b3b3b; }
        """
    else:
        return """
            QWidget { background-color: #f0f0f0; color: #000000; }
            QLineEdit, QTextEdit { background-color: #ffffff; border: 1px solid #cccccc; }
            QPushButton { background-color: #2196f3; padding: 5px; }
            QPushButton:hover { background-color: #42a5f5; }
            QComboBox { background-color: #ffffff; border: 1px solid #cccccc; padding: 5px; }
            QTabBar::tab { background-color: #e0e0e0; color: #000000; }
            QTabBar::tab:selected { background-color: #ffffff; }
        """

def set_output_text_style(widget, theme='dark'):
    if theme == 'dark':
        widget.setStyleSheet("""
            QTextEdit, QListWidget {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                color: white;
                padding: 5px;
            }
        """)
    else:
        widget.setStyleSheet("""
            QTextEdit, QListWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                color: black;
                padding: 5px;
            }
        """)

print("GUI_settings module loaded")  # Debug print
