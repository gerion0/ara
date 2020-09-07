// vim: set noet ts=4 sw=4:

#include "value_analysis.h"

#include "common/llvm_common.h"

#include <Graphs/GenericGraph.h>
#include <Graphs/VFGNode.h>
#include <SVF-FE/PAGBuilder.h>
#include <Util/BasicTypes.h>
#include <WPA/Andersen.h>
#include <boost/property_tree/json_parser.hpp>
#include <boost/python.hpp>
#include <llvm/ADT/GraphTraits.h>

using namespace boost::property_tree;
using namespace SVF;

namespace ara::step {
	void ValueAnalysis::retrieve_value(const SVFG& vfg, const llvm::Value& value, graph::Argument& arg) {
		// logger.debug() << "Trying to get value of " << value << std::endl;
		PAG* pag = PAG::getPAG();
		SVF::Andersen* ander = SVF::AndersenWaveDiff::createAndersenWaveDiff(pag);
		SVF::PTACallGraph* s_callgraph = ander->getPTACallGraph();

		PAGNode* pNode = pag->getPAGNode(pag->getValueNode(&value));
		assert(pNode != nullptr);
		const VFGNode* vNode = vfg.getDefSVFGNode(pNode);
		assert(vNode != nullptr);

		graph::CallGraph callgraph = graph.get_callgraph();

		std::stack<VFGContainer> nodes;

		nodes.emplace(VFGContainer(vNode, graph::CallPath()));

		while (!nodes.empty()) {
			VFGContainer current = std::move(nodes.top());
			nodes.pop();
			const VFGNode* current_node = current.node;
			// copy
			graph::CallPath next_path = current.call_path;
			logger.info() << "CallPath: " << next_path << std::endl;

			for (VFGNode::const_iterator it = current_node->InEdgeBegin(); it != current_node->InEdgeEnd(); ++it) {
				VFGEdge* edge = *it;
				logger.info() << "Next edge: " << *edge << std::endl;
				if (auto cde = llvm::dyn_cast<CallDirSVFGEdge>(edge)) {
					const CallBlockNode* cbn = s_callgraph->getCallSite(cde->getCallSiteId());
					assert(s_callgraph->hasCallGraphEdge(cbn) && "no call graph edge found");
					auto bi = s_callgraph->getCallEdgeBegin(cbn);
					const SVF::PTACallGraphEdge* call_site = *bi;
					bi++;
					assert(bi == s_callgraph->getCallEdgeEnd(cbn) && "more than one edge found");
					assert(call_site->getCallSiteID() == cde->getCallSiteId() && "call side IDs does not match.");
					logger.info() << "Callsite: " << *call_site << std::endl;
					next_path.add_call_site(callgraph, safe_deref(call_site));
				}

				const VFGNode* next_node = (*it)->getSrcNode();
				bool last_node = false;
				if (auto stmt = llvm::dyn_cast<StmtVFGNode>(next_node)) {
					const PAGEdge* edge = stmt->getPAGEdge();
					if (const Constant* c = llvm::dyn_cast<Constant>(edge->getValue())) {
						logger.info() << "Constant: " << *c << std::endl;
						// We have a problem here. SVF gives us a constant Value what is meaningful from their site.
						// However, we want to fill this into our Argument structure which is exposed in Python. In
						// Python there exists no thing like const correctness because is semantically useless. That
						// means that we are forced to limit the Python types to only support methods that don't violate
						// const correctness or do a const_cast here and hope that everything will work.
						arg.add_variant(next_path, const_cast<Constant&>(*c));
						last_node = true;
					}
				}

				if (!last_node && next_node != nullptr) {
					logger.info() << "Next node: " << *next_node << std::endl;
					nodes.emplace(VFGContainer(next_node, next_path));
				}
				next_path = current.call_path;
			}
		}
	}

	void ValueAnalysis::collectUsesOnVFG(const SVFG& vfg, const llvm::CallBase& call, graph::Arguments& args) {
		if (isCallToLLVMIntrinsic(&call)) {
			throw ValuesUnknown("Called function is an intrinsic.");
		}

		llvm::AttributeList attrl = call.getAttributes();

		int t = 0;
		for (const llvm::Use& use : call.args()) {
			const Value* val = use.get();
			llvm::AttributeSet attrs = attrl.getAttributes(t + 1);

			assert(val != nullptr);
			logger.debug() << "retrieving value: \033[35m" << *val << "\033[0m" << std::endl;
			std::shared_ptr<graph::Argument> arg = graph::Argument::get(attrs);
			retrieve_value(vfg, *val, *arg);
			args.emplace_back(arg);
		}
	}

	std::shared_ptr<graph::Arguments> ValueAnalysis::get_value(const llvm::CallBase& called_func, const SVFG& vfg) {
		std::shared_ptr<graph::Arguments> args = graph::Arguments::get();
		llvm::AttributeSet attrs;
		llvm::Function* func = called_func.getCalledFunction();
		if (func) {
			// this->logger.debug() << *bb << std::endl;
			// this->logger.debug() << "Called function: " << *called_func << std::endl;
			this->logger.debug() << "Function name: \033[34m" << func->getName().str() << "\033[0m" << std::endl;
			this->logger.debug() << "Number of args: " << func->arg_size() << std::endl;
			this->logger.debug() << "------------" << std::endl;
			// llvm::AttributeSet attrs = func->getAttributes().getFnAttributes();
			llvm::AttributeList attrl = called_func.getAttributes();
			for (unsigned it = attrl.index_begin(); it != attrl.index_end(); ++it) {
				// index is sometimes negative (2**32 - 1 or something)??
				// logger.debug() << it << ": " << attrl.getAsString(it) << std::endl;
			}

			const llvm::ConstantTokenNone* token = llvm::ConstantTokenNone::get(called_func.getContext());
			const llvm::Constant* none_c = llvm::dyn_cast<llvm::Constant>(token);

			collectUsesOnVFG(vfg, called_func, *args);
		}

		/* return value */
		if (called_func.hasOneUse()) {
			const llvm::User* ur = called_func.user_back();
			llvm::Value* retval = ur->getOperand(1);
			logger.debug() << "return: " << *retval << std::endl;
			args->set_return_value(graph::Argument::get(llvm::AttributeSet(), *retval));
		}

		this->logger.debug() << "Retrieved " << args->size() << " arguments for call " << called_func << std::endl;
		this->logger.debug() << "================================================" << std::endl;
		std::cout << std::endl;
		return args;
	}

	llvm::json::Array ValueAnalysis::get_configured_dependencies() {
		const auto& entry_point_name = entry_point.get();
		assert(entry_point_name && "Entry point argument not given");
		return llvm::json::Array{llvm::json::Object{{{"name", "Syscall"}, {"entry_point", *entry_point_name}}}};
	}

	std::string ValueAnalysis::get_description() {
		return "Perform a value analysis for all system calls (core step).";
	}

	void ValueAnalysis::init_options() {
		EntryPointStep<ValueAnalysis>::init_options();
		dump_stats = dump_stats_template.instantiate(get_name());
		opts.emplace_back(dump_stats);
	}

	void ValueAnalysis::run() {
		graph::CFG cfg = graph.get_cfg();
		const auto& prefix = dump_prefix.get();
		const auto& entry_point_name = entry_point.get();
		assert(entry_point_name && "Entry point argument not given");

		SVFG& svfg = graph.get_svfg();
		svfg.dump("svfgdump");

		graph_tool::gt_dispatch<>()([&](auto& g) { this->get_values(g, svfg); },
		                            graph_tool::always_directed())(cfg.graph.get_graph_view());
	}
} // namespace ara::step
