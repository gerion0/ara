// vim: set noet ts=4 sw=4:

#pragma once

#include "option.h"
#include "step.h"

#include <graph.h>

namespace ara::step {
	class LoadFreeRTOSConfig : public Step {
	  private:
		virtual void fill_options() override;

	  public:
		virtual std::string get_name() const override { return "LoadFreeRTOSConfig"; }
		virtual std::string get_description() const override;
		virtual std::vector<std::string> get_dependencies() override { return {"SysFuncts"}; }

		virtual void run(graph::Graph& graph) override;
	};
} // namespace ara::step