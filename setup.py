# setup.py
from setuptools import setup

setup(
    name='jriver-voice-command',
    version='0.2.0',
    py_modules=['jriver_voice', 'config', 'model_manager'],
    data_files=[('', ['config.json'])],  # Include config.json in the package
    install_requires=[
        'vosk',
        'pyaudio',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'jriver-voice=jriver_voice:main', 
        ],
    },
)
