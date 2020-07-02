// vim: set noet ts=4 sw=4:

#pragma once

#include "option.h"
#include "step.h"

#include <graph.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/Value.h>

namespace ara::step {
	class ReplaceSyscallsCreate : public ConfStep<ReplaceSyscallsCreate> {
	  private:
		using ConfStep<ReplaceSyscallsCreate>::ConfStep;
		bool handle_tcb_ref_param(llvm::IRBuilder<>& Builder, llvm::Value* tcb_ref, llvm::Value* the_tcb);
		bool replace_call_with_true(llvm::CallBase* call);
		llvm::Function* get_fn(const char* name);

	  public:
		static std::string get_name() { return "ReplaceSyscallsCreate"; }
		static std::string get_description();

		virtual void run() override;

		bool replace_mutex_create_static(uintptr_t where, char* symbol_metadata);
		bool replace_mutex_create_initialized(uintptr_t where, char* symbol_metadata);
		bool replace_queue_create_static(uintptr_t where, char* symbol_metadata, char* symbol_storage);
		bool replace_queue_create_initialized(uintptr_t where, char* symbol_metadata);
		bool replace_task_create_static(uintptr_t where, char* handle_name, char* stack_name);
		bool replace_task_create_initialized(uintptr_t where, char* handle_name);
	};
} // namespace ara::step
