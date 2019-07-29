// vim: set noet ts=4 sw=4:

#include "llvm_basic_optimization.h"

#include "llvm_common.h"

#include <iostream>
#include <list>
#include <llvm/Analysis/AssumptionCache.h>
#include <llvm/Analysis/BasicAliasAnalysis.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Dominators.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/PassManager.h>
#include <llvm/Passes/PassBuilder.h>
#include <llvm/Support/Casting.h>
#include <llvm/Support/Debug.h>
#include <llvm/Support/raw_os_ostream.h>
#include <llvm/Transforms/InstCombine/InstCombine.h>
#include <llvm/Transforms/Scalar.h>
#include <llvm/Transforms/Scalar/DCE.h>
#include <llvm/Transforms/Scalar/GVN.h>
#include <llvm/Transforms/Scalar/Reassociate.h>
#include <llvm/Transforms/Scalar/SimplifyCFG.h>

namespace step {
	using namespace llvm;

	std::string LLVMBasicOptimization::get_description() const {
		return "Perform some basic optimizations passes from llvm."
		  "\n";
	}

	std::vector<std::string> LLVMBasicOptimization::get_dependencies() {
		return {"IRReader"};
	}

	void LLVMBasicOptimization::run(graph::Graph& graph) {
		//		DebugFlag = true; // enable llvm passes output
		llvm::Module& module = graph.new_graph.get_module();
		auto& theContext = module.getContext();

		// Collect own set of transformations
		FunctionPassManager fpm(true);
		// Do simple "peephole" optimizations and bit-twiddling optzns.
		fpm.addPass(InstCombinePass());
		// Reassociate expressions.
		fpm.addPass(ReassociatePass());
		// Eliminate Common SubExpressions.
		fpm.addPass(GVN());
		// Simplify the control flow graph (deleting unreachable blocks, etc).
		fpm.addPass(SimplifyCFGPass());
		// Remove dead code generated by the previous passes
		fpm.addPass(DCEPass());

		// Register some analyses to be keept up to date during transformations
		FunctionAnalysisManager FAM;
		FAM.registerPass([&] { return AssumptionAnalysis(); });
		FAM.registerPass([&] { return DominatorTreeAnalysis(); });
		FAM.registerPass([&] { return BasicAA(); });
		FAM.registerPass([&] { return TargetLibraryAnalysis(); });

		// Alternatively: use standard set of optimizations
		PassBuilder PB;
		PB.registerFunctionAnalyses(FAM);
		auto fpm2 = PB.buildFunctionSimplificationPipeline(PassBuilder::OptimizationLevel::O1,
		                                                   PassBuilder::ThinLTOPhase::None, true);

		for (auto& function : module) {
			if (function.empty())
				continue;
			// function.viewCFG();
			// Apply own set of optimizations
			// fpm.run(function, FAM);

			// Alternatively: apply default set of Optimizations
			fpm2.run(function, FAM);

			function.viewCFG();
		}
	}
} // namespace step
