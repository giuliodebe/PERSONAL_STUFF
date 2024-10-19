import PyInstaller.__main__
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'Main.py',
    '--name=GEngineering_Robotics_App',
    '--onedir',  # Changed from --onefile
    '--windowed',
    '--noupx',
    '--clean',
    f'--add-data={os.path.join(current_dir, "instructions.pdf")}:.',
    '--icon=app_icon.ico',
    '--add-data=GUI_settings.py:.',
    '--add-data=Target_converter.py:.',
    '--add-data=orientation_converter.py:.',
    '--add-data=ip_configurator.py:.',
    '--add-data=Robot_Mov_Parser.py:.',
])