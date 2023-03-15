// SPDX-FileCopyrightText: 2020 Gerion Entrup <entrup@sra.uni-hannover.de>
//
// SPDX-License-Identifier: GPL-3.0-or-later

// vim: set noet ts=4 sw=4:

#include "common/llvm_common.h"
#include "test.h"

#include <graph.h>
#include <iostream>
#include <llvm/IR/Instructions.h>
#include <llvm/Support/Casting.h>
#include <stdexcept>
#include <string>

namespace ara::step {
	std::string CompInsertTest::get_name() { return "CompInsertTest"; }

	std::string CompInsertTest::get_description() { return "Step for testing the CompInsert step"; }

	void CompInsertTest::run() {
		llvm::Module& module = graph.get_module();
		for (auto& f : module) {
			for (auto& b : f) {
				for (auto& i : b) {
					bool found_double_call = false;
					if (llvm::isa<llvm::CallBase>(i) && !is_call_to_intrinsic(i)) {
						if (found_double_call) {
							std::string call;
							llvm::raw_string_ostream rso(call);
							i.print(rso);
							logger.err() << "Found call that is following another call: " << call << std::endl;
							throw std::runtime_error("Found call that is not in extra basic block.");
						}
						found_double_call = true;
					}
				}
			}
		}
	}

	std::vector<std::string> CompInsertTest::get_single_dependencies() { return {"CompInsert"}; }
} // namespace ara::step
