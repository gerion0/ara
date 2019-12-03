// vim: set noet ts=4 sw=4:

#include "const_prop.h"
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Transforms/Scalar.h>

namespace ara::step {
    using namespace llvm;
	std::string ConstProp::get_description() const {
		return "Performs Constant Propagation."
		       "\n"
		       "Uses the LLVM Simple Constant Propagation pass to substitute the values of known constants inside of expressions.";
	}

    std::vector<std::string> ConstProp::get_dependencies() { return {"IRReader"}; }

	//void ConstantPropagation::fill_options() { opts.emplace_back(dummy_option); }

	void ConstProp::run(graph::Graph& graph) {
        Module& module = graph.get_module();
        legacy::FunctionPassManager fpm(&module);
        fpm.add(createConstantPropagationPass()); 
        fpm.doInitialization();

    /* Loop over module's functions and count how many functions are altered by the ConstProp Pass.
       fpm.run(function) returns true when a function was modified. */
        int n = 0;
        int i = 0;
        for (auto& function : module) {
            if (function.empty())
                continue;

            // Remove function's Attribute that prevents it's optimization
            if (function.hasOptNone()) {
                function.removeFnAttr(Attribute::OptimizeNone);
            }

            logger.debug() << "Function " << i << " before pass execution:\n" << std::endl;
            function.dump();
            if(fpm.run(function)) {
                logger.debug() << "The function was modified.\n" << std::endl;
                ++n;
            }
            logger.debug() << "Function " << i << " after pass execution:\n" << std::endl;
            function.dump();
            ++i;
        }
		logger.debug() << "Constant Propagation step finished successfully. " << n << "/" << module.getFunctionList().size() << " functions modified." << std::endl;
	}
} // namespace ara::step
