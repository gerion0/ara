# SPDX-FileCopyrightText: 2021 Bastian Fuhlenriede
# SPDX-FileCopyrightText: 2021 Gerion Entrup <entrup@sra.uni-hannover.de>
# SPDX-FileCopyrightText: 2022 Jan Neugebauer
#
# SPDX-License-Identifier: GPL-3.0-or-later

from carguments cimport CallPath
from libcpp cimport bool
from libcpp.memory cimport unique_ptr
from libcpp.vector cimport vector
from libcpp.string cimport string
from common.backported_utility cimport pair
from ir cimport Value, GetElementPtrInst

from libc.stdint cimport uint64_t

cimport cgraph

cdef extern from "value_analyzer.h" namespace "ara::cython":
    cdef void raise_py_valueerror()

cdef extern from "value_analyzer.h" namespace "ara::step":
    cdef cppclass ValueAnalyzer:
        @staticmethod
        unique_ptr[ValueAnalyzer] get(cgraph.Graph, object, object)

        object py_get_argument_value(object, CallPath, unsigned, int, object) except +raise_py_valueerror
        object py_get_return_value(object, CallPath) except +raise_py_valueerror
        object py_get_memory_value(Value*, CallPath) except +raise_py_valueerror
        object py_get_assignments(Value*, const vector[GetElementPtrInst*], CallPath) except +raise_py_valueerror
        void py_assign_system_object(Value*, uint64_t, const vector[GetElementPtrInst*], CallPath&) except +raise_py_valueerror
        bool py_has_connection(object, CallPath, unsigned, uint64_t) except +raise_py_valueerror
        object py_find_global(string) except +raise_py_valueerror
