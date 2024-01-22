from setuptools import setup

setup(
    name='e3v3se_display',
    version='0.1',
    packages=['e3v3se_display'],
    entry_points={
        'console_scripts': [
            'e3v3se_display = run:main',
        ],
    },
    install_requires=[
        'argparse',
        'configparser',
        'requests',
        'pyserial',
        'websocket-client',
       
    ],
)
