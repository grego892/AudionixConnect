from setuptools import setup, find_packages

setup(
    name="audionix_connect",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pylivewire>=1.0.0",
        "aes67>=0.1.0",
        "python-rtp>=0.0.7",
        "opus>=0.2.0",
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
