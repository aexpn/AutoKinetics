# distutils: language = c++

from libcpp.string cimport string
from libcpp cimport bool

cdef extern from "../cpp/core.hpp" namespace "autokinetics":
    string get_hello_message()

def hello():
    """
    Ruft die C++-Funktion auf und gibt den String als Python-Str zurück.
    """
    cdef string cpp_msg = get_hello_message()
    # Umwandeln in Python str
    return cpp_msg.decode("utf-8") if hasattr(cpp_msg, "decode") else cpp_msg.c_str()
