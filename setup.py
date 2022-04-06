# coding: utf-8

import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()
	
setuptools.setup(
    name="pyuwb",
    version="0.0.7",
    author="jiangshan00000",
    author_email="710806594@qq.com",
    description="A uwb locating library",
	long_description=long_description,
	long_description_content_type = "text/markdown",
    url="https://github.com/Jiangshan00001/pyuwb",
    packages=setuptools.find_packages(),
    install_requires=['pyserial'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
    'console_scripts': [
        'pyuwb = pyuwb:console_cmd',
        'pyuwb_qt = pyuwb:gui_cmd',
    ],
    'gui_scripts': [
        'pyuwb_qt = pyuwb:gui_cmd',
    ]
    },

)