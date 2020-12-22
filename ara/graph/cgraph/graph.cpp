#include "graph.h"

#include "common/exceptions.h"

#include <Python.h>
#include <boost/python.hpp>
#include <cassert>
#include <exception>
#include <iostream>

namespace ara::graph {
	graph_tool::GraphInterface& get_graph(PyObject* py_obj) {
		PyObject* pyobj_graph = PyObject_GetAttrString(py_obj, "_Graph__graph");
		assert(pyobj_graph != nullptr);
		boost::python::extract<graph_tool::GraphInterface&> get_graph_interface(pyobj_graph);
		assert(get_graph_interface.check());
		return get_graph_interface();
	}

	// ABB functions
	const llvm::CallBase* CFG::get_call_base(const ABBType type, const llvm::BasicBlock& bb) const {
		if (!(type == ABBType::call || type == ABBType::syscall)) {
			return nullptr;
		}
		const llvm::CallBase* call = llvm::dyn_cast<llvm::CallBase>(&bb.front());
		assert(call);
		return call;
	}

	const std::string CFG::bb_get_call(const ABBType type, const llvm::BasicBlock& bb) const {
		auto call = get_call_base(type, bb);
		if (!call) {
			return "";
		}
		const llvm::Function* func = call->getCalledFunction();
		// function are sometimes values with alias to a function
		if (!func) {
			const llvm::Value* value = call->getCalledValue();
			if (const llvm::Constant* alias = llvm::dyn_cast<llvm::Constant>(value)) {
				if (llvm::Function* tmp_func = llvm::dyn_cast<llvm::Function>(alias->getOperand(0))) {
					func = tmp_func;
				}
			}
		}
		if (!func) {
			return "";
		}
		return func->getName();
	}

	bool CFG::bb_is_indirect(const ABBType type, const llvm::BasicBlock& bb) const {
		auto call = get_call_base(type, bb);
		if (!call) {
			return false;
		}
		return call->isIndirectCall();
	}

	template <class Property>
	Property get_property(PyObject* prop_dict, const char* key) {
		PyObject* prop = PyObject_GetItem(prop_dict, PyUnicode_FromString(key));
		assert(prop != nullptr);

		PyObject* prop_any = PyObject_CallMethod(prop, "_get_any", nullptr);
		assert(prop_any != nullptr);

		boost::python::extract<boost::any> get_property(prop_any);
		assert(get_property.check());

		try {
			return boost::any_cast<Property>(get_property());
		} catch (boost::bad_any_cast& e) {
			std::cerr << "Bad any cast for attribute '" << key << "'" << std::endl;
			throw e;
		}
	}

	PyObject* get_vprops(PyObject* graph) {
		PyObject* vprops = PyObject_GetAttrString(graph, "vertex_properties");
		assert(vprops != nullptr);
		return vprops;
	}

	PyObject* get_eprops(PyObject* graph) {
		PyObject* eprops = PyObject_GetAttrString(graph, "edge_properties");
		assert(eprops != nullptr);
		return eprops;
	}

	inline void create_properties(CFG& cfg, PyObject* py_cfg) {
#define ARA_MAP(Graph, Value, Type) Graph.Value = get_property<decltype(Graph.Value)>(Type, #Value);
#define ARA_VMAP(Value) ARA_MAP(cfg, Value, vprops)
#define ARA_EMAP(Value) ARA_MAP(cfg, Value, eprops)

		PyObject* vprops = get_vprops(py_cfg);

		ARA_VMAP(name)
		ARA_VMAP(type)
		ARA_VMAP(is_function)
		ARA_VMAP(entry_bb)
		ARA_VMAP(exit_bb)
		ARA_VMAP(is_exit)
		ARA_VMAP(is_exit_loop_head)
		ARA_VMAP(part_of_loop)
		ARA_VMAP(file)
		ARA_VMAP(line)
		ARA_VMAP(implemented)
		ARA_VMAP(syscall)
		ARA_VMAP(function)
		ARA_VMAP(arguments)
		ARA_VMAP(call_graph_link)

		PyObject* eprops = get_eprops(py_cfg);

		cfg.etype = get_property<decltype(cfg.etype)>(eprops, "type");
		ARA_EMAP(is_entry)

#undef ARA_VMAP
#undef ARA_EMAP
	}

	CFG CFG::get(PyObject* py_cfg) {
		assert(py_cfg != nullptr);
		CFG cfg(get_graph(py_cfg));
		create_properties(cfg, py_cfg);
		return cfg;
	}

	struct CFG::CFGUniqueEnabler : public CFG {
		template <typename... Args>
		CFGUniqueEnabler(Args&&... args) : CFG(std::forward<Args>(args)...) {}
	};

	std::unique_ptr<CFG> CFG::get_ptr(PyObject* py_cfg) {
		assert(py_cfg != nullptr);
		std::unique_ptr<CFG> cfg = std::make_unique<CFGUniqueEnabler>(get_graph(py_cfg));
		create_properties(*cfg, py_cfg);
		return cfg;
	}

	CFG Graph::get_cfg() {
		// extract self.cfg from Python
		PyObject* pycfg = PyObject_GetAttrString(graph, "cfg");
		assert(pycfg != nullptr);

		return CFG::get(pycfg);
	}

	std::unique_ptr<CFG> Graph::get_cfg_ptr() {
		// extract self.cfg from Python
		PyObject* pycfg = PyObject_GetAttrString(graph, "cfg");
		assert(pycfg != nullptr);

		return CFG::get_ptr(pycfg);
	}

	os::OS Graph::get_os() {
		PyObject* os = PyObject_GetAttrString(graph, "os");
		assert(os != Py_None && "OS must be set.");
		return os::OS(os);
	}

	inline void create_properties(CallGraph& callgraph, PyObject* py_callgraph) {
		PyObject* vprops = get_vprops(py_callgraph);

#define ARA_VMAP(Value) ARA_MAP(callgraph, Value, vprops)
#define ARA_EMAP(Value) ARA_MAP(callgraph, Value, eprops)

		ARA_VMAP(function)
		ARA_VMAP(function_name)
		ARA_VMAP(svf_vlink)

		// syscall categories
#define ARA_SYS_ACTION(Value) ARA_VMAP(syscall_category_##Value)
#include "syscall_category.inc"
#undef ARA_SYS_ACTION

		PyObject* eprops = get_eprops(py_callgraph);

		ARA_EMAP(callsite)
		ARA_EMAP(callsite_name)
		ARA_EMAP(svf_elink)

#undef ARA_VMAP
#undef ARA_EMAP

		// TODO: the cfg graph attribute is not mappable with the above method. Fix it, when necessary.
	}

	CallGraph CallGraph::get(PyObject* py_callgraph) {
		assert(py_callgraph != nullptr);
		CallGraph callgraph(get_graph(py_callgraph));
		create_properties(callgraph, py_callgraph);
		return callgraph;
	}

	struct CallGraph::CallGraphUniqueEnabler : public CallGraph {
		template <typename... Args>
		CallGraphUniqueEnabler(Args&&... args) : CallGraph(std::forward<Args>(args)...) {}
	};

	std::unique_ptr<CallGraph> CallGraph::get_ptr(PyObject* py_callgraph) {
		assert(py_callgraph != nullptr);
		std::unique_ptr<CallGraph> callgraph = std::make_unique<CallGraphUniqueEnabler>(get_graph(py_callgraph));
		create_properties(*callgraph, py_callgraph);
		return callgraph;
	}

	CallGraph Graph::get_callgraph() {
		// extract self.callgraph from Python
		PyObject* pycallgraph = PyObject_GetAttrString(graph, "callgraph");
		assert(pycallgraph != nullptr);

		return CallGraph::get(pycallgraph);
	}

	std::unique_ptr<CallGraph> Graph::get_callgraph_ptr() {
		// extract self.callgraph from Python
		PyObject* pycallgraph = PyObject_GetAttrString(graph, "callgraph");
		assert(pycallgraph != nullptr);

		return CallGraph::get_ptr(pycallgraph);
	}

	inline void create_properties(InstanceGraph& instancegraph, PyObject* py_instancegraph) {
		PyObject* vprops = get_vprops(py_instancegraph);

#define ARA_VMAP(Value) ARA_MAP(instancegraph, Value, vprops)
#define ARA_EMAP(Value) ARA_MAP(instancegraph, Value, eprops)

		ARA_VMAP(label)
		ARA_VMAP(obj)
		ARA_VMAP(id)
		ARA_VMAP(branch)
		ARA_VMAP(loop)
		ARA_VMAP(after_scheduler)
		ARA_VMAP(unique)
		ARA_VMAP(soc)
		ARA_VMAP(llvm_soc)
		ARA_VMAP(file)
		ARA_VMAP(line)
		ARA_VMAP(specialization_level)

		PyObject* eprops = get_eprops(py_instancegraph);
		
		// FIXME: Mapping fails for some reason
		// ARA_EMAP(elabel)

#undef ARA_VMAP
#undef ARA_EMAP
#undef ARA_MAP
	}

	InstanceGraph InstanceGraph::get(PyObject* py_instancegraph) {
		assert(py_instancegraph != nullptr);
		InstanceGraph instancegraph(get_graph(py_instancegraph));
		create_properties(instancegraph, py_instancegraph);
		return instancegraph;
	}

	struct InstanceGraph::InstanceGraphUniqueEnabler : public InstanceGraph {
		template <typename... Args>
		InstanceGraphUniqueEnabler(Args&&... args) : InstanceGraph(std::forward<Args>(args)...) {}
	};

	std::unique_ptr<InstanceGraph> InstanceGraph::get_ptr(PyObject* py_instancegraph) {
		assert(py_instancegraph != nullptr);
		std::unique_ptr<InstanceGraph> instancegraph =
		    std::make_unique<InstanceGraphUniqueEnabler>(get_graph(py_instancegraph));
		create_properties(*instancegraph, py_instancegraph);
		return instancegraph;
	}

	InstanceGraph Graph::get_instances() {
		// extract self.instances from Python
		PyObject* pyinstancegraph = PyObject_GetAttrString(graph, "instances");
		assert(pyinstancegraph != nullptr);

		return InstanceGraph::get(pyinstancegraph);
	}

	std::unique_ptr<InstanceGraph> Graph::get_instances_ptr() {
		// extract self.instances from Python
		PyObject* pyinstancegraph = PyObject_GetAttrString(graph, "instances");
		assert(pyinstancegraph != nullptr);

		return InstanceGraph::get_ptr(pyinstancegraph);
	}
} // namespace ara::graph
