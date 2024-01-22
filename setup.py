from setuptools import setup, find_packages

setup(
    name='e3v3se_display_klipper',
    version='0.1',
    packages=find_packages(where='src'),  # Finds packages under the 'src' directory
    package_dir={'': 'src'},  # Specifies that the package root is 'src'

    entry_points={
        'console_scripts': [
            'e3v3se_display_klipper = e3v3se_display.run:main',
        ],
    },
    install_requires=[
        'argparse',
        'configparser',
        'requests',
        'pyserial',
        'websocket-client',
        'multitimer'
       
    ],
)
