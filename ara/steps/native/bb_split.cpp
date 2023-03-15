// SPDX-FileCopyrightText: 2020 Gerion Entrup <entrup@sra.uni-hannover.de>
//
// SPDX-License-Identifier: GPL-3.0-or-later

// vim: set noet ts=4 sw=4:

#include "bb_split.h"

#include "common/llvm_common.h"

#include <iostream>
#include <list>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/raw_os_ostream.h>

namespace ara::step {
	using namespace llvm;

	std::string BBSplit::get_description() { return "Split basic blocks in function call and computation blocks."; }

	std::vector<std::string> BBSplit::get_single_dependencies() { return {"CompInsert"}; }

	void BBSplit::run() {
		llvm::Module& module = graph.get_module();
		unsigned split_counter = 0;

		for (auto& function : module) {
			std::list<BasicBlock*> bbs;
			for (BasicBlock& _bb : function) {
				bbs.push_back(&_bb);
			}

			for (BasicBlock* bb : bbs) {
				BasicBlock::iterator it = bb->begin();
				while (it != bb->end()) {
					while (isa<CallBase>(*it)) {
						if (is_call_to_intrinsic(*it)) {
							++it;
							continue;
						}
						// split before call instruction
						std::stringstream ss;
						ss << "BB" << split_counter++;
						bb = bb->splitBasicBlock(it, ss.str());
						it = bb->begin();

						++it;

						if (it == bb->end()) {
							goto while_end;
						}

						if (isa<CallBase>(*it) && (!is_call_to_intrinsic(*it))) {
							continue;
						}

						// split after call instruction
						ss.str("");
						ss << "BB" << split_counter++;
						bb = bb->splitBasicBlock(it, ss.str());
						it = bb->begin();
					}
					++it;
				while_end:;
				}
			}
		}
		logger.debug() << "Split " << split_counter << " basic blocks." << std::endl;
	}
} // namespace ara::step
