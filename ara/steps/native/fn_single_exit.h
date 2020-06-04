// vim: set noet ts=4 sw=4:

#pragma once

#include "step.h"

#include <graph.h>
#include <llvm/IR/BasicBlock.h>
#include <string>

namespace ara::step {

	class FnSingleExit : public Step {
	  private:
		void fill_unreachable_and_exit(llvm::BasicBlock*& unreachable, llvm::BasicBlock*& exit,
		                               llvm::BasicBlock& probe) const;

	  public:
		virtual std::string get_name() const override { return "FnSingleExit"; }
		virtual std::string get_description() const override;
		virtual std::vector<std::string> get_dependencies() override;

		virtual void run(graph::Graph& graph) override;
	};
} // namespace ara::step