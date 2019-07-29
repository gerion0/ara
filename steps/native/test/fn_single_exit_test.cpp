// vim: set noet ts=4 sw=4:

#include "test.h"

#include "llvm/IR/Instructions.h"
#include "llvm/Support/Casting.h"

#include <iostream>
#include <string>
#include <stdexcept>

#include "graph.h"

namespace step {
	std::string FnSingleExitTest::get_name() const { return "FnSingleExitTest"; }

	std::string FnSingleExitTest::get_description() const { return "Step for testing the FnSingleExit step"; }

	void FnSingleExitTest::run(graph::Graph& graph) {
		llvm::Module& module = graph.new_graph.get_module();
 		unsigned split_counter = 0;

		bool fail = false;
 		for (auto &function : module) {
			std::list<llvm::BasicBlock *> exit_blocks;
			for (llvm::BasicBlock& _bb : function) {
				if (succ_begin(&_bb) == succ_end(&_bb)) {
					exit_blocks.push_back(&_bb);
				}
 			}

			if (exit_blocks.size() > 1) {
				logger.err() << "Found Function with " << exit_blocks.size() << " exit nodes:" << std::endl;
				logger.err() << function.getName().str()<<std::endl;
				for (llvm::BasicBlock* bb: exit_blocks) {
					logger.err() << "exit block: " << bb->getName().str() << std::endl;
				}
				function.viewCFG();
				fail = true;
			}
		}
		if (fail) {
			throw std::runtime_error("Found function with two exit BBs.");
		}
	}

	std::vector<std::string> FnSingleExitTest::get_dependencies() { return {"FnSingleExit"}; }
} // namespace step
