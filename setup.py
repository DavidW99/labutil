from setuptools import setup, find_packages

setup(
    name="labutil",
    version="0.2.0",
    author="Boris Kozinsky",
    python_requires=">=3.7",
    packages=find_packages(include=["labutil", "labutil.*"]),
    install_requires=["ase", "numpy"],
    zip_safe=True,
)
