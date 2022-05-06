from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(name="snap_cursor_stack",
      version="1.0.0",
      packages=["snap_cursor_stack"],
      install_requires=requirements)
