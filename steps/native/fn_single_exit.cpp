// vim: set noet ts=4 sw=4:

#include "fn_single_exit.h"

#include "common/llvm_common.h"

#include <iostream>
#include <list>
#include <llvm/Analysis/LoopInfo.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/raw_os_ostream.h>
#include <llvm/Transforms/Utils/BasicBlockUtils.h>

namespace ara::step {
	using namespace llvm;

	std::string FnSingleExit::get_description() const { return "Find unique exit BB and endless loops for functions"; }

	std::vector<std::string> FnSingleExit::get_dependencies() { return {"BBSplit"}; }

	void FnSingleExit::run(graph::Graph& graph) {
		graph::LLVMData& llvm_data = graph.get_llvm_data();
		for (auto& function : llvm_data.get_module()) {
			if (function.empty() || function.isIntrinsic()) {
				continue;
			}

			// exit block detection
			// an exit block is a block with no successors
			BasicBlock* exit_block = nullptr;
			for (BasicBlock& _bb : function) {
				if (succ_begin(&_bb) == succ_end(&_bb)) {
					if (exit_block != nullptr) {
						logger.err() << "Function: " << function.getName().str() << " has multiple exit blocks."
						             << std::endl;
						logger.debug() << "Basicblock 1 with exit: " << *exit_block << std::endl;
						logger.debug() << "Basicblock 2 with exit: " << _bb << std::endl;
						assert(false && "ARA expects that the UnifyFunctionExitNodes pass was executed.");
					}
					exit_block = &_bb;
				}
			}
			llvm_data.functions[&function].exit_block = exit_block;
			llvm_data.basic_blocks[exit_block].is_exit_block = true;

			// endless loop detection
			DominatorTree dom_tree = DominatorTree(function);
			LoopInfoBase<BasicBlock, Loop> loop_info;

			dom_tree.updateDFSNumbers();
			loop_info.analyze(dom_tree);

			bool loop_found = false;
			for (const Loop* loop : loop_info) {
				SmallVector<BasicBlock*, 6> vec;
				loop->getExitBlocks(vec);
				if (vec.size() != 0) {
					continue;
				}
				// we have an endless loop
				llvm_data.functions[&function].endless_loops.emplace_back(loop->getHeader());
				llvm_data.basic_blocks[loop->getHeader()].is_loop_head = true;
				loop_found = true;
			}

			// some nice printing
			if (exit_block) {
				if (loop_found) {
					logger.debug() << "Function " << function.getName().str()
					               << " has an regular exit and endless loops." << std::endl;
				} else {
					logger.debug() << "Function " << function.getName().str() << " has exactly one regular exit."
					               << std::endl;
				}
			} else {
				if (loop_found) {
					logger.debug() << "Function " << function.getName().str() << " ends in an endless loop."
					               << std::endl;
				} else {
					logger.warn() << "Function " << function.getName().str()
					              << " neither has an exit block nor ends in an endless loop." << std::endl;
				}
			}
		}
	}
} // namespace ara::step
