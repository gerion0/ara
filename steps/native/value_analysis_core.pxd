cimport cgraph

from libcpp.string cimport string
from libcpp.vector cimport vector

cdef extern from "value_analysis_core.h" namespace "ara::step":
    cdef cppclass ValueAnalysisCore:
        ValueAnalysis(dict config) except +
        string get_name()
        string get_description()
        vector[string] get_dependencies()
        void run(cgraph.Graph a)