import sys
import logging
import ctypes
import os
import psutil
import subprocess
import re
import ipaddress
import socket
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QStatusBar, 
                             QComboBox, QLineEdit, QCheckBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import sys
import logging
import ctypes
import os
import psutil
import subprocess
import re
import ipaddress
import socket
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QStatusBar, 
                             QComboBox, QLineEdit, QCheckBox, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import GUI settings
from GUI_settings import (set_dark_theme, set_light_theme, set_button_style, 
                          set_title_font, set_input_field_style, set_output_text_style,
                          set_common_stylesheet)

class IPConfiguratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP Address Configurator")
        
        # Set regular dimensions
        self.regular_width = 400
        self.regular_height = 500  # Reduced height due to removal of log area
        
        # Calculate maximum dimensions (20% larger)
        self.max_width = int(self.regular_width * 1.2)
        self.max_height = int(self.regular_height * 1.2)
        
        # Set initial size and maximum size
        self.setGeometry(100, 100, self.regular_width, self.regular_height)
        self.setMaximumSize(self.max_width, self.max_height)
        
        # Set up the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        # Create UI elements
        self.create_ui()
        
        # Set up logging (file only, no console output)
        logging.basicConfig(filename='ip_configurator.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Populate network interfaces
        self.populate_network_interfaces()
        
        # Initial update of IP fields
        if self.interface_combo.count() > 0:
            self.update_ip_fields()

        # Set initial theme
        self.current_theme = 'dark'
        self.apply_theme()

    def create_ui(self):
        # Add title label with custom font
        self.title_label = QLabel("IP Address Configurator")
        self.title_label.setAlignment(Qt.AlignCenter)
        set_title_font(self.title_label)
        self.layout.addWidget(self.title_label)
        
        # Add space between elements
        self.layout.addSpacing(20)
        
        # Interface selection
        self.interface_label = QLabel("Select Interface:")
        self.layout.addWidget(self.interface_label)
        self.interface_combo = QComboBox()
        self.layout.addWidget(self.interface_combo)
        self.interface_combo.currentIndexChanged.connect(self.update_ip_fields)
        
        # IP Address input
        self.ip_label = QLabel("IP Address:")
        self.layout.addWidget(self.ip_label)
        self.ip_entry = QLineEdit()
        self.layout.addWidget(self.ip_entry)
        
        # Subnet Mask input
        self.subnet_label = QLabel("Subnet Mask:")
        self.layout.addWidget(self.subnet_label)
        self.subnet_entry = QLineEdit()
        self.layout.addWidget(self.subnet_entry)
        
        # Gateway input
        self.gateway_label = QLabel("Default Gateway:")
        self.layout.addWidget(self.gateway_label)
        self.gateway_entry = QLineEdit()
        self.layout.addWidget(self.gateway_entry)
        
        # DNS input
        self.dns_label = QLabel("DNS Server:")
        self.layout.addWidget(self.dns_label)
        self.dns_entry = QLineEdit()
        self.layout.addWidget(self.dns_entry)
        
        # DHCP checkbox
        self.dhcp_checkbox = QCheckBox("Use DHCP")
        self.dhcp_checkbox.stateChanged.connect(self.toggle_ip_fields)
        self.layout.addWidget(self.dhcp_checkbox)
        
        # Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply_button)

        # Add a refresh button
        self.refresh_button = QPushButton("Refresh Interfaces")
        self.refresh_button.clicked.connect(self.populate_network_interfaces)
        self.layout.addWidget(self.refresh_button)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def populate_network_interfaces(self):
        interfaces = self.get_network_interfaces()
        self.interface_combo.clear()
        for interface, status, ip in interfaces:
            self.interface_combo.addItem(f"{interface} - {status} - {ip or 'No IP'}")
        if interfaces:
            self.interface_combo.setCurrentIndex(0)
            self.update_ip_fields()
        else:
            QMessageBox.warning(self, "No Interfaces", "No active network interfaces detected. Please check your network connections.")


    def get_network_interfaces(self):
        interfaces = []
        try:
            for nic, addrs in psutil.net_if_addrs().items():
                if self.is_valid_interface(nic):
                    status = self.get_interface_status(nic)
                    ip = self.get_interface_ip(addrs)
                    interfaces.append((nic, status, ip))
            
            logging.info(f"Detected {len(interfaces)} interfaces")
        except Exception as e:
            logging.error(f"Error detecting network interfaces: {str(e)}")
        
        return interfaces
    
    def is_valid_interface(self, nic):
        try:
            # Check if the interface is up and running
            return psutil.net_if_stats()[nic].isup
        except Exception:
            return False

    def get_current_ip_config(self, interface):
        try:
            config = {
                "ip": "",
                "subnet": "",
                "gateway": "",
                "dns": ""
            }
            
            # Get IP, subnet, and gateway
            ip_config = subprocess.check_output(f'netsh interface ipv4 show config name="{interface}"', shell=True, stderr=subprocess.DEVNULL, universal_newlines=True)
            
            ip_match = re.search(r"IP Address:\s+(\d+\.\d+\.\d+\.\d+)", ip_config)
            if ip_match:
                config["ip"] = ip_match.group(1)
            
            subnet_match = re.search(r"Subnet Prefix:\s+(\d+\.\d+\.\d+\.\d+)", ip_config)
            if subnet_match:
                config["subnet"] = subnet_match.group(1)
            
            gateway_match = re.search(r"Default Gateway:\s+(\d+\.\d+\.\d+\.\d+)", ip_config)
            if gateway_match:
                config["gateway"] = gateway_match.group(1)
            
            # Get DNS
            dns_config = subprocess.check_output(f'netsh interface ipv4 show dns name="{interface}"', shell=True, stderr=subprocess.DEVNULL, universal_newlines=True)
            dns_match = re.search(r"Statically Configured DNS Servers:\s+(\d+\.\d+\.\d+\.\d+)", dns_config)
            if dns_match:
                config["dns"] = dns_match.group(1)
            else:
                config["dns"] = "Automatic"
            
            logging.info(f"Retrieved current config for {interface}")
            return config
        except subprocess.CalledProcessError as e:
            logging.error(f"Error executing netsh command for {interface}: {str(e)}")
            return {"ip": "", "subnet": "", "gateway": "", "dns": ""}
        except Exception as e:
            logging.error(f"Error getting IP config for {interface}: {str(e)}")
            return {"ip": "", "subnet": "", "gateway": "", "dns": ""}
    
    def update_ip_fields(self):
        selected_item = self.interface_combo.currentText()
        interface = selected_item.split(' - ')[0]
        current_config = self.get_current_ip_config(interface)
        self.ip_entry.setText(current_config["ip"])
        self.subnet_entry.setText(current_config["subnet"])
        self.gateway_entry.setText(current_config["gateway"])
        self.dns_entry.setText(current_config["dns"])

        # Log the updated configuration to the file only
        logging.info(f"Updated configuration for {interface}: {current_config}")


    def toggle_ip_fields(self):
        enabled = not self.dhcp_checkbox.isChecked()
        self.ip_entry.setEnabled(enabled)
        self.subnet_entry.setEnabled(enabled)
        self.gateway_entry.setEnabled(enabled)
        self.dns_entry.setEnabled(enabled)

    def apply_settings(self):
        interface = self.interface_combo.currentText()
        if self.dhcp_checkbox.isChecked():
            self.set_dhcp(interface)
        else:
            ip_address = self.ip_entry.text()
            subnet_mask = self.subnet_entry.text()
            gateway = self.gateway_entry.text()
            dns = self.dns_entry.text()
            self.set_static_ip(interface, ip_address, subnet_mask, gateway, dns)

    def set_static_ip(self, interface, ip_address, subnet_mask, gateway, dns):
        interface = interface.split(' - ')[0]  # Extract the interface name
        if not is_admin():
            QMessageBox.warning(self, "Admin Rights Required", "Please run this application as an administrator to change IP settings.")
            return

        try:
            # Set IP address, subnet mask, and gateway
            command = f'netsh interface ipv4 set address name="{interface}" static {ip_address} {subnet_mask} {gateway}'
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)

            # Handle DNS setting
            if dns:
                dns_command = f'netsh interface ipv4 set dns name="{interface}" static {dns}'
            else:
                dns_command = f'netsh interface ipv4 set dns name="{interface}" dhcp'
            subprocess.run(dns_command, shell=True, check=True, capture_output=True, text=True)

            self.statusBar.showMessage("Static IP configuration applied", 3000)
            
            # Verify the changes
            new_config = self.get_current_ip_config(interface)
            if new_config['ip'] != ip_address:
                QMessageBox.warning(self, "Verification Failed", f"IP Address change verification failed. Current IP: {new_config['ip']}")

            # Update the IP fields after setting static IP
            self.update_ip_fields()

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to set static IP: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def get_interface_ip(self, addrs):
        for addr in addrs:
            if addr.family == socket.AF_INET:
                return addr.address
        return "No IP"
    
    def get_interface_status(self, interface):
        try:
            stats = psutil.net_if_stats()[interface]
            addrs = psutil.net_if_addrs()[interface]
            
            if stats.isup:
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('169.254'):
                        return "Connected"
                return "Enabled (No IP)"
            else:
                return "Disabled"
        except Exception:
            return "Unknown"

    def set_dhcp(self, interface):
        interface = interface.split(' - ')[0]  # Extract the interface name
        try:
            # Set IP to DHCP
            ip_command = f'netsh interface ipv4 set address name="{interface}" source=dhcp'
            subprocess.run(ip_command, shell=True, check=True, capture_output=True, text=True)

            # Set DNS to DHCP
            dns_command = f'netsh interface ipv4 set dns name="{interface}" source=dhcp'
            subprocess.run(dns_command, shell=True, check=True, capture_output=True, text=True)

            self.statusBar.showMessage("Switched to DHCP", 3000)
            
            # Wait for a moment to allow DHCP to assign new settings
            QApplication.processEvents()
            import time
            time.sleep(2)  # Wait for 2 seconds

            # Update the IP fields after switching to DHCP
            self.update_ip_fields()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to switch to DHCP: {str(e)}")


    def validate_ip(self, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    def apply_theme(self):
        if self.current_theme == 'dark':
            set_dark_theme(self)
        else:
            set_light_theme(self)

        # Apply common stylesheet
        self.setStyleSheet(set_common_stylesheet(self.current_theme))

        # Apply specific styles
        set_button_style(self.apply_button, self.current_theme)
        set_button_style(self.refresh_button, self.current_theme)
        set_input_field_style(self.ip_entry, self.current_theme)
        set_input_field_style(self.subnet_entry, self.current_theme)
        set_input_field_style(self.gateway_entry, self.current_theme)
        set_input_field_style(self.dns_entry, self.current_theme)
        set_input_field_style(self.interface_combo, self.current_theme)

    def set_theme(self, theme):
        self.current_theme = theme
        self.apply_theme()
   
    def log_message(self, message):
        """
        Log a message to the file only, not to the UI.
        """
        logging.info(message)

    def closeEvent(self, event):
        event.accept()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == '__main__':
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        app = QApplication(sys.argv)
        main_window = IPConfiguratorApp()
        main_window.show()
        sys.exit(app.exec_())