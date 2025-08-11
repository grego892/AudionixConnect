from setuptools import setup, find_packages

setup(
    name="audionix_connect",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "dpkt>=1.9.7",
        "pyaudio>=0.2.11",
        "python-rtsp>=0.0.14",
        "opuslib>=3.0.1",
        "sounddevice>=0.4.5",
        "numpy>=1.21.0",
        "click>=8.0.0",
        "PyYAML>=6.0",
        "pydantic>=1.9.0",
    ],
    entry_points={
        "console_scripts": [
            "audionix-connect=audionix_connect.cli:main",
        ],
    },
)
