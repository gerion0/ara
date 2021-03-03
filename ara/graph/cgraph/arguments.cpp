#include "arguments.h"

#include "common/llvm_common.h"
#include "graph_data_pyx_wrapper.h"

#include <llvm/Support/raw_ostream.h>

namespace boost::detail {
	std::size_t hash_value(const boost::detail::adj_edge_descriptor<long unsigned int>& edge) {
		std::size_t seed = 0;
		boost::hash_combine(seed, edge.s);
		boost::hash_combine(seed, edge.t);
		boost::hash_combine(seed, edge.idx);
		return seed;
	}
} // namespace boost::detail

namespace ara::graph {
	std::string CallPath::get_callsite_name(const SVF::PTACallGraphEdge& edge) const {
		if (!(edge.isIndirectCallEdge() | edge.isDirectCallEdge())) {
			return "";
		}
		const SVF::PTACallGraphEdge::CallInstSet& calls =
		    (edge.isIndirectCallEdge()) ? edge.getIndirectCalls() : edge.getDirectCalls();

		if (calls.size() != 1) {
			return "";
		}

		const SVF::CallBlockNode* node = *calls.begin();
		assert(node != nullptr && "call is null");
		const llvm::Instruction* inst = node->getCallSite();
		assert(inst != nullptr && "inst is null");

		return llvm_to_string(*inst);
	}

	void CallPath::check_and_assign(std::shared_ptr<CallGraph> call_graph) {
		if (this->call_graph) {
			assert(&call_graph->graph == &this->call_graph->graph && "Different call graphs are not supported.");
		} else {
			this->call_graph = call_graph;
		}
	}

	void CallPath::add_call_site(PyObject* call_graph, PyObject* edge) {
		check_and_assign(std::make_shared<CallGraph>(CallGraph::get(call_graph)));
		graph_tool::EdgeBase& edge_base = boost::python::extract<graph_tool::EdgeBase&>(edge);
		edges.emplace_back(edge_base.get_descriptor());
	}

	template <class G>
	void foo(SVF::PTACallGraphEdge** edge, graph::CallGraph& callgraph, graph_tool::GraphInterface::edge_t o_edge) {
		*edge = const_cast<SVF::PTACallGraphEdge*>(callgraph.get_svf_elink<G>(o_edge));
	}

	const SVF::PTACallGraphEdge* CallPath::svf_at(size_t index) const {
		assert(call_graph != nullptr && "CallGraph must not be null");
		SVF::PTACallGraphEdge* edge = nullptr;
		graph_tool::gt_dispatch<>()(
		    [&](auto& g) {
			    edge = const_cast<SVF::PTACallGraphEdge*>(
			        call_graph->get_svf_elink<typename std::remove_reference<decltype(g)>::type>(this->at(index)));
		    },
		    graph_tool::always_directed())(call_graph->graph.get_graph_view());
		return edge;
	}

	PyObject* CallPath::py_at(size_t index) {
		if (is_empty()) {
			throw std::out_of_range("CallPath has no elements.");
		}
		assert(call_graph != nullptr && "call graph is not initialized");
		auto gi = call_graph->graph;
		boost::python::object new_e;
		graph_tool::run_action<>()(gi, [&](auto&& graph) {
			return get_call_site_dispatched(std::forward<decltype(graph)>(graph), gi, index, new_e);
		})();
		return boost::python::incref(new_e.ptr());
	}

	std::string CallPath::print(bool call_site, bool instruction, bool functions) const {
		if (!(call_site || instruction || functions) || is_empty()) {
			return "CallPath()";
		}
		assert(call_graph != nullptr && "call graph is not initialized");
		std::stringstream ss;
		graph_tool::gt_dispatch<>()(
		    [&](auto& g) { print_dispatched(g, *call_graph, call_site, instruction, functions, ss); },
		    graph_tool::always_directed())(call_graph->graph.get_graph_view());
		return ss.str();
	}

	bool CallPath::operator==(const CallPath& other) const {
		if (edges.size() != other.edges.size()) {
			return false;
		}
		for (const auto& pair : boost::combine(edges, other.edges)) {
			if (pair.get<0>() != pair.get<1>()) {
				return false;
			}
		}
		return true;
	}

	void CallPath::pop_front() {
		if (is_empty()) {
			return;
		}
		edges.erase(edges.begin());
	}

	void CallPath::pop_back() {
		if (is_empty()) {
			return;
		}
		edges.pop_back();
	}

	bool CallPath::is_recursive() const {
		if (is_empty()) {
			return false;
		}
		assert(call_graph != nullptr && "call graph is not initialized");
		bool ret_value = false;
		graph_tool::gt_dispatch<>()([&](auto& g) { is_recursive_dispatched(g, ret_value); },
		                            graph_tool::always_directed())(call_graph->graph.get_graph_view());
		return ret_value;
	}

	std::ostream& operator<<(std::ostream& os, const CallPath& cp) {
		os << cp.print(/* call_site = */ true, /* instruction = */ false, /* functions = */ true);
		return os;
	}

	struct Argument::ArgumentSharedEnabler : public Argument {
		template <typename... Args>
		ArgumentSharedEnabler(Args&&... args) : Argument(std::forward<Args>(args)...) {}
	};
	std::shared_ptr<Argument> Argument::get(const llvm::AttributeSet& attrs) {
		return std::make_shared<ArgumentSharedEnabler>(attrs);
	}
	std::shared_ptr<Argument> Argument::get(const llvm::AttributeSet& attrs, llvm::Value& value) {
		return std::make_shared<ArgumentSharedEnabler>(attrs, value);
	}

	bool Argument::is_constant() const {
		for (const auto& value : values) {
			if (!llvm::isa<llvm::Constant>(value.second)) {
				return false;
			}
		}
		return true;
	}

	bool Argument::has_value(const CallPath& key) const { return values.find(key) != values.end(); }

	llvm::Value& Argument::get_value(const CallPath& key) const {
		if (is_determined()) {
			return values.begin()->second;
		}
		auto it = values.find(key);
		if (it != values.end()) {
			return it->second;
		}

		// copy key
		CallPath r_key = key;

		// check for less specific paths
		while (!r_key.is_empty()) {
			r_key.pop_front();
			auto it = values.find(r_key);
			if (it != values.end()) {
				return it->second;
			}
		}
		throw std::out_of_range("Argument has no such value.");
	}

	std::ostream& operator<<(std::ostream& os, const Argument& arg) {
		os << "Argument(";
		if (arg.size() == 0) {
			os << "empty)";
			return os;
		}
		if (arg.is_determined()) {
			os << llvm_to_string(arg.get_value());
		} else {
			bool first = true;
			for (const auto& entry : arg) {
				if (!first) {
					os << ", ";
				}
				first = false;

				os << entry.first << ": " << llvm_to_string(entry.second);
			}
		}

		os << ", constant=";
		if (arg.is_constant()) {
			os << "true";
		} else {
			os << "false";
		}

		os << ")";
		return os;
	}

	std::ostream& operator<<(std::ostream& os, const Arguments& args) {
		os << "Arguments(";
		bool first = true;
		for (const auto& arg : args) {
			if (!first) {
				os << ", ";
			}
			first = false;
			if (arg == nullptr) {
				os << "nullptr";
			} else {
				os << *arg;
			}
		}
		if (args.has_return_value()) {
			os << ", return_value=" << *args.get_return_value();
		}
		os << ")";
		return os;
	}

	PyObject* Arguments::get_python_obj() { return py_get_arguments(shared_from_this()); }
} // namespace ara::graph
