import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sdf_timing",
    version="0.0.1",
    author="SymbiFlow Authors",
    author_email="symbiflow@lists.librecores.org",
    description="Python library for working Standard Delay Format (SDF) Timing Annotation files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SymbiFlow/python-sdf-timing",
    packages=setuptools.find_packages(),
    install_requires=['ply', 'pyjson'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: ISC License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['sdf_timing_parse=sdf_timing.sdfparse:main'],
    },
)
