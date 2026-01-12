from setuptools import setup, find_packages
import os

version = "2.1.0"
if os.path.exists("VERSION"):
    with open("VERSION", "r") as f:
        version = f.read().strip()

setup(
    name="simco_agent",
    version=version,
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "requests>=2.25.0",
        "cryptography>=35.0.0",
        "scapy>=2.4.5",
        "PyYAML>=6.0"
    ],
    entry_points={
        "console_scripts": [
            "simco-agent=simco_agent.__main__:main",
        ],
    },
)
