from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "autokinetics_binding",
        sources=["python/autokinetics_binding.pyx"],
        language="c++",
        include_dirs=["cpp"],  
    )
]

setup(
    name="autokinetics",
    ext_modules=cythonize(extensions),
)
