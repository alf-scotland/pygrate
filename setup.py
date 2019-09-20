from setuptools import setup, find_packages

setup(
    name='pygrate', 
    packages=find_packages(),
    install_requires=[
        'xlsxwriter',
        'openpyxl'
    ],
    entry_points = {
        'console_scripts': [
            'pygrate-create=pygrate.create:main'
            'pygrate-migrate=pygrate.migrate:main'
        ],
    }
)