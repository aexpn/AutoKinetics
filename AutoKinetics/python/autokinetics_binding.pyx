# -*- coding: utf-8 -*-
# distutils: language = c++

from libcpp.string import string

cdef extern from "core.hpp" namespace "autokinetics":
    string get_hello_message()

def hello():
    """
    Ruft die C++-Funktion auf und gibt den String zurück.
    """
    cdef string cpp_message = get_hello_message()
    return cpp_message.decode('utf-8')
