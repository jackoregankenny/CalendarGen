from setuptools import setup, find_packages

setup(
    name="calendargen",
    version="0.1.0",
    package_dir={"": "src"},  # Tell setuptools packages are under src
    packages=find_packages(where="src"),  # Find packages under src
    install_requires=[
        'reportlab>=4.0.0',
        'flask>=3.0.0',
        'werkzeug>=3.0.0',
    ],
    python_requires='>=3.8',
)