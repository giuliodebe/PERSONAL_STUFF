import sys
import logging
import os
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QMenuBar, QMenu, QAction,
                             QStatusBar, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit,
                             QToolBar, QSizePolicy, QFrame, QTabWidget, QCheckBox, QTabBar,
                             QStylePainter, QStyleOptionTab, QStyle, QMdiArea, QMdiSubWindow)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QRect, QPoint, QSize, pyqtSignal, QEvent, QMimeData
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QColor, QMouseEvent, QPalette, QBrush, QDrag

from GUI_settings import (set_dark_theme, set_light_theme, set_button_style, set_title_font,
                          set_common_stylesheet)

from Target_converter import TargetConverterApp
from ip_configurator import IPConfiguratorApp
from Robot_Mov_Parser import RobotMovementParser

# Add the parent directory of GRobotics to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now you can import from GRobotics
from GRobotics.orientation_converter import OrientationConverter

# At the top of your file, after imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLOSE_ICON_PATH = os.path.join(SCRIPT_DIR, "close.png")

class CloseableTabBar(QTabBar):
    tabCloseRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setElideMode(Qt.ElideRight)
        self.setExpanding(False)
        self._close_button_size = 16

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        if index != 0:  # Add space for close button on all tabs except the first
            size.setWidth(size.width() + self._close_button_size)
        return size

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionTab()

        for index in range(self.count()):
            self.initStyleOption(option, index)
            tab_rect = self.tabRect(index)
            
            if index != 0:  # Adjust tab rect for close button on all tabs except the first (Home tab)
                tab_rect.adjust(0, 0, -self._close_button_size, 0)

            painter.drawControl(QStyle.CE_TabBarTabShape, option)
            painter.drawText(tab_rect, Qt.AlignCenter | Qt.AlignVCenter, self.tabText(index))

            if index != 0:  # Draw close button on all tabs except the first (Home tab)
                close_button_rect = self.get_close_button_rect(self.tabRect(index))
                close_icon = QIcon(CLOSE_ICON_PATH)
                close_icon.paint(painter, close_button_rect, Qt.AlignCenter)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            for index in range(self.count()):
                if index != 0 and self.get_close_button_rect(self.tabRect(index)).contains(event.pos()):
                    self.tabCloseRequested.emit(index)
                    return
        super().mousePressEvent(event)

    def get_close_button_rect(self, tab_rect):
        return QRect(tab_rect.right() - self._close_button_size, tab_rect.center().y() - self._close_button_size // 2,
                     self._close_button_size, self._close_button_size)

class DetachableTabBar(QTabBar):
    tabDetachRequested = pyqtSignal(int, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setElideMode(Qt.ElideRight)
        self.setSelectionBehaviorOnRemove(QTabBar.SelectLeftTab)
        self.setMovable(True)
        self.dragStartPosition = None

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        if index != -1 and index != 0:  # Ignore double-clicks on the home tab
            self.tabDetachRequested.emit(index, event.globalPos())
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if self.tabAt(event.pos()) == 0:
            return  # Ignore mouse press on home tab
        self.dragStartPosition = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.dragStartPosition:
            return
        if self.tabAt(self.dragStartPosition) == 0:
            return  # Prevent dragging home tab
        if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragStartPosition = None
        super().mouseReleaseEvent(event)

class DetachableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabBar = DetachableTabBar(self)
        self.setTabBar(self.tabBar)
        self.tabBar.tabDetachRequested.connect(self.detachTab)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.detachedTabs = {}
        self.hiddenTabs = {}
        print("DetachableTabWidget initialized")

    def closeTab(self, index):
        if index != 0 and self.count() > 1:
            widget = self.widget(index)
            if widget in self.detachedTabs:
                self.detachedTabs[widget].close()
                del self.detachedTabs[widget]
            self.removeTab(index)
            print(f"Tab at index {index} closed")

    def tabInserted(self, index):
        if index == 0:
            self.tabBar.setTabButton(0, QTabBar.RightSide, None)
            print("Home tab inserted, close button removed")

    def detachTab(self, index, point):
        if index == 0:  # Prevent detaching home tab
            return

        name = self.tabText(index)
        icon = self.tabIcon(index)
        
        # Get the content widget
        content_widget = self.widget(index)
        
        # Create a new instance of the content widget
        new_content_widget = content_widget.__class__()
        
        # Create a new DetachedTab
        detached_tab = DetachedTab(new_content_widget, name, self, content_widget)
        detached_tab.setWindowIcon(icon)
        detached_tab.move(point)
        detached_tab.show()
        
        # Store reference and hide the tab
        self.detachedTabs[content_widget] = detached_tab
        self.hiddenTabs[content_widget] = {'index': index, 'name': name, 'icon': icon}
        self.removeTab(index)
        
        print(f"Tab '{name}' detached")

    def attachTab(self, original_widget, name):
        if original_widget in self.detachedTabs:
            detached_tab = self.detachedTabs[original_widget]
            del self.detachedTabs[original_widget]
            detached_tab.close()

        if original_widget in self.hiddenTabs:
            hidden_info = self.hiddenTabs[original_widget]
            index = self.insertTab(hidden_info['index'], original_widget, hidden_info['icon'], hidden_info['name'])
            del self.hiddenTabs[original_widget]
        else:
            index = self.addTab(original_widget, name)
        
        self.setCurrentIndex(index)
        print(f"Tab '{name}' reattached")

class DetachedTab(QMainWindow):
    def __init__(self, content_widget, name, parent_tabwidget, original_widget):
        super().__init__(None)
        self.setWindowTitle(name)
        self.content_widget = content_widget
        self.parent_tabwidget = parent_tabwidget
        self.original_widget = original_widget
        self.setCentralWidget(content_widget)
        self.resize(800, 600)
        self.installEventFilter(self)
        print(f"DetachedTab '{name}' created")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Close:
            print(f"DetachedTab '{self.windowTitle()}' closing, reattaching")
            self.parent_tabwidget.attachTab(self.original_widget, self.windowTitle())
            return True
        return super().eventFilter(obj, event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GEngineering Robotics App")
        self.setGeometry(100, 100, 800, 600)
        
        self.setMinimumSize(800, 600)
        
        self.target_converter = None
        self.orientation_converter = None
        self.ip_configurator = None
        self.robot_movement_parser = None

        self.create_menu_bar()
        self.create_search_bar()
        self.create_central_widget()
        self.create_home_tab()  # Make sure this is called to create the home tab
        self.create_footer()

        self.current_theme = 'dark'
        self.apply_theme()

        self.statusBar().showMessage("Ready")

        logging.basicConfig(filename='app.log', level=logging.INFO)

        self.tool_instances = {}

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        target_converter_action = QAction('Target Converter', self)
        target_converter_action.triggered.connect(self.open_target_converter)
        tools_menu.addAction(target_converter_action)
        
        orientation_converter_action = QAction('Orientation Converter', self)
        orientation_converter_action.triggered.connect(self.open_orientation_converter)
        tools_menu.addAction(orientation_converter_action)
        
        ip_configurator_action = QAction('IP Address Configurator', self)
        ip_configurator_action.triggered.connect(self.open_ip_configurator)
        tools_menu.addAction(ip_configurator_action)
        
        robot_movement_parser_action = QAction('Robot Movement Parser', self)
        robot_movement_parser_action.triggered.connect(self.open_robot_movement_parser)
        tools_menu.addAction(robot_movement_parser_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        # Create Appearance submenu
        appearance_menu = QMenu('Appearance', self)
        settings_menu.addMenu(appearance_menu)
        
        dark_theme_action = QAction('Dark Theme', self)
        dark_theme_action.setShortcut('Ctrl+D')
        dark_theme_action.triggered.connect(lambda: self.set_theme('dark'))
        appearance_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction('Light Theme', self)
        light_theme_action.setShortcut('Ctrl+L')
        light_theme_action.triggered.connect(lambda: self.set_theme('light'))
        appearance_menu.addAction(light_theme_action)

        # Help menu
        help_menu = menubar.addMenu('Help')
        
        instructions_action = QAction('Instructions', self)
        instructions_action.setShortcut('Ctrl+I')
        instructions_action.setStatusTip('Open instructions PDF')
        instructions_action.triggered.connect(self.open_instructions)
        help_menu.addAction(instructions_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def create_search_bar(self):
        search_toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, search_toolbar)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        search_toolbar.addWidget(spacer)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tools and functionalities...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_menu_items)
        search_toolbar.addWidget(self.search_input)

    def create_central_widget(self):
        self.central_widget = DetachableTabWidget(self)
        self.setCentralWidget(self.central_widget)
        print("Central widget (DetachableTabWidget) created")

    def create_home_tab(self):
        home_tab = QWidget()
        layout = QVBoxLayout(home_tab)

        # Set background image using QLabel
        background_label = QLabel(home_tab)
        background_pixmap = QPixmap(os.path.join(SCRIPT_DIR, "background.png"))
        background_label.setPixmap(background_pixmap)
        background_label.setScaledContents(True)
        background_label.setGeometry(0, 0, self.width(), self.height())

        # Create a semi-transparent panel for ABB manual search
        abb_search_panel = QFrame(home_tab)
        abb_search_panel.setObjectName("abb_search_panel")
        abb_search_layout = QVBoxLayout(abb_search_panel)

        abb_search_label = QLabel("ABB Robotics Manual Search:")
        abb_search_layout.addWidget(abb_search_label)

        self.abb_search_input = QLineEdit()
        self.abb_search_input.setPlaceholderText("Search ABB robotics manuals...")
        abb_search_layout.addWidget(self.abb_search_input)

        abb_search_button = QPushButton("Search")
        abb_search_button.clicked.connect(self.search_abb_manuals)
        abb_search_layout.addWidget(abb_search_button)

        # Add the search panel to the main layout
        layout.addWidget(abb_search_panel)

        layout.addStretch(1)  # Add stretch to push widgets to the top

        self.central_widget.addTab(home_tab, "Home")
        print("Home tab added")

        # Connect resize event to update background size
        home_tab.resizeEvent = lambda event: background_label.setGeometry(0, 0, event.size().width(), event.size().height())

    def create_footer(self):
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)

        self.log_label = QLabel("Log: Ready")
        self.log_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        footer_layout.addWidget(self.log_label)

        footer_layout.addStretch()

        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        footer_layout.addWidget(self.clock_label)

        self.statusBar().addPermanentWidget(footer_widget, 1)

        self.update_clock()
        self.start_clock()

    def start_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)

    def update_clock(self):
        current_time = QDateTime.currentDateTime().toString('dddd, MMMM d, yyyy hh:mm:ss A')
        self.clock_label.setText(current_time)

    def open_instructions(self):
        instructions_path = os.path.join(os.path.dirname(__file__), 'instructions.pdf')
        if os.path.exists(instructions_path):
            webbrowser.open('file://' + instructions_path)
            self.statusBar().showMessage("Instructions opened", 3000)
        else:
            self.show_error_message("Instructions file not found.")
            logging.error("Instructions file not found.")

    def open_recent_file(self, file):
        self.statusBar().showMessage(f"Opening recent file: {file}", 3000)
        # Implement the logic to open the recent file

    def set_theme(self, theme):
        self.current_theme = theme
        self.apply_theme()
        self.update_open_tabs_theme()
        self.statusBar().showMessage(f"{theme.capitalize()} theme applied", 3000)

    def apply_theme(self):
        if self.current_theme == 'dark':
            set_dark_theme(self)
            base_color = "#2b2b2b"
            text_color = "#ffffff"
            hover_color = "#3a3a3a"
        else:
            set_light_theme(self)
            base_color = "#ffffff"
            text_color = "#000000"
            hover_color = "#e0e0e0"

        # Set custom stylesheet for the main window and its widgets
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {base_color};
                color: {text_color};
            }}
            QMenuBar {{
                background-color: {base_color};
                color: {text_color};
            }}
            QMenuBar::item:selected {{
                background-color: {hover_color};
            }}
            QMenu {{
                background-color: {base_color};
                color: {text_color};
            }}
            QMenu::item:selected {{
                background-color: {hover_color};
            }}
            QTabWidget::pane {{
                border: 1px solid {text_color};
                background-color: {base_color};
            }}
            QTabBar::tab {{
                background-color: {base_color};
                color: {text_color};
                border: 1px solid {text_color};
                padding: 5px;
                padding-right: 20px;
            }}
            QTabBar::tab:selected {{
                background-color: {hover_color};
            }}
            QTabBar::close-button {{
                image: url({CLOSE_ICON_PATH});
                subcontrol-position: right;
            }}
            QTabBar::close-button:hover {{
                background-color: #ff0000;
                border-radius: 8px;
            }}
            QLineEdit, QPushButton {{
                background-color: {base_color};
                color: {text_color};
                border: 1px solid {text_color};
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            #abb_search_panel {{
                background-color: rgba(123, 63, 0, 200);  // Dark red color with some transparency
                border-radius: 5px;
                padding: 10px;
                margin: 20px;
            }}
            #abb_search_panel QLabel, #abb_search_panel QLineEdit, #abb_search_panel QPushButton {{
                color: white;
            }}
        """)

        # Update child themes if necessary
        self.update_child_themes()
    
    def update_button_styles(self):
        """Update styles for buttons based on the current theme."""
        for button in self.tool_buttons.values():
            set_button_style(button, self.current_theme)
    
    def update_child_themes(self):
        """Update the theme for child windows if they exist."""
        if self.target_converter:
            self.target_converter.set_theme(self.current_theme)
        if self.orientation_converter:
            self.orientation_converter.set_theme(self.current_theme)
        if self.ip_configurator:
            self.ip_configurator.set_theme(self.current_theme)
        if self.robot_movement_parser:
            self.robot_movement_parser.set_theme(self.current_theme)
    
    def open_target_converter(self):
        for i in range(self.central_widget.count()):
            if self.central_widget.tabText(i) == "Target Converter":
                self.central_widget.setCurrentIndex(i)
                return

        if "Target Converter" not in self.tool_instances:
            self.tool_instances["Target Converter"] = TargetConverterApp()
        
        target_converter = self.tool_instances["Target Converter"]
        self.central_widget.addTab(target_converter, "Target Converter")
        self.central_widget.setCurrentIndex(self.central_widget.count() - 1)

    def open_orientation_converter(self):
        for i in range(self.central_widget.count()):
            if self.central_widget.tabText(i) == "Orientation Converter":
                self.central_widget.setCurrentIndex(i)
                return

        if "Orientation Converter" not in self.tool_instances:
            self.tool_instances["Orientation Converter"] = OrientationConverter()
        
        orientation_converter = self.tool_instances["Orientation Converter"]
        self.central_widget.addTab(orientation_converter, "Orientation Converter")
        self.central_widget.setCurrentIndex(self.central_widget.count() - 1)

    def open_ip_configurator(self):
        for i in range(self.central_widget.count()):
            if self.central_widget.tabText(i) == "IP Configurator":
                self.central_widget.setCurrentIndex(i)
                return

        if "IP Configurator" not in self.tool_instances:
            self.tool_instances["IP Configurator"] = IPConfiguratorApp()
        
        ip_configurator = self.tool_instances["IP Configurator"]
        ip_configurator.set_theme(self.current_theme)
        self.central_widget.addTab(ip_configurator, "IP Configurator")
        self.central_widget.setCurrentIndex(self.central_widget.count() - 1)

    def open_robot_movement_parser(self):
        for i in range(self.central_widget.count()):
            if self.central_widget.tabText(i) == "Robot Movement Parser":
                self.central_widget.setCurrentIndex(i)
                return

        if "Robot Movement Parser" not in self.tool_instances:
            self.tool_instances["Robot Movement Parser"] = RobotMovementParser()
        
        robot_movement_parser = self.tool_instances["Robot Movement Parser"]
        robot_movement_parser.set_theme(self.current_theme)
        self.central_widget.addTab(robot_movement_parser, "Robot Movement Parser")
        self.central_widget.setCurrentIndex(self.central_widget.count() - 1)

    def show_about_dialog(self):
        QMessageBox.about(self, "About", "GEngineering Robotics App\nVersion 1.0\n© 2023 GEngineering")

    def closeEvent(self, event):
        if self.target_converter:
            self.target_converter.close()
        if self.orientation_converter:
            self.orientation_converter.close()
        if self.ip_configurator:
            self.ip_configurator.close()
        if self.robot_movement_parser:
            self.robot_movement_parser.close()  # Add this line
        event.accept()

    def show_error_message(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec_()
        logging.error(message)

    def filter_menu_items(self, text):
        for menu in self.menuBar().findChildren(QMenu):
            self.filter_menu(menu, text.lower())

    def filter_menu(self, menu, search_text):
        for action in menu.actions():
            if action.menu():
                # If the action is a submenu, recursively filter it
                self.filter_menu(action.menu(), search_text)
                # Show/hide the submenu based on whether it has visible actions
                action.setVisible(any(a.isVisible() for a in action.menu().actions()))
            else:
                # For regular menu items, check if the search text is in the action text
                action.setVisible(search_text in action.text().lower())

        # Show/hide the menu based on whether it has visible actions
        menu.menuAction().setVisible(any(a.isVisible() for a in menu.actions()))

    def search_abb_manuals(self):
        search_query = self.abb_search_input.text()
        if search_query:
            url = f"https://new.abb.com/search/en/results#query={search_query}"
            webbrowser.open(url)
            self.statusBar().showMessage(f"Searching ABB manuals for: {search_query}", 3000)
        else:
            self.show_error_message("Please enter a search term for ABB manuals.")

    def update_open_tabs_theme(self):
        for i in range(self.central_widget.count()):
            tab = self.central_widget.widget(i)
            if hasattr(tab, 'set_theme'):
                tab.set_theme(self.current_theme)
            elif hasattr(tab, 'layout'):
                self.update_tab_widgets_theme(tab)

    def update_tab_widgets_theme(self, tab):
        if tab.layout() is not None:
            for i in range(tab.layout().count()):
                widget = tab.layout().itemAt(i).widget()
                if widget is not None and hasattr(widget, 'set_theme'):
                    widget.set_theme(self.current_theme)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
