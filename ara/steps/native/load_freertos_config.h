// SPDX-FileCopyrightText: 2020 Björn Fiedler <fiedler@sra.uni-hannover.de>
// SPDX-FileCopyrightText: 2020 Gerion Entrup <entrup@sra.uni-hannover.de>
//
// SPDX-License-Identifier: GPL-3.0-or-later

// vim: set noet ts=4 sw=4:

#pragma once

#include "option.h"
#include "step.h"

#include <graph.h>

namespace ara::step {
	class LoadFreeRTOSConfig : public ConfStep<LoadFreeRTOSConfig> {
	  private:
		using ConfStep<LoadFreeRTOSConfig>::ConfStep;

	  public:
		static std::string get_name() { return "LoadFreeRTOSConfig"; }
		static std::string get_description();

		virtual std::vector<std::string> get_single_dependencies() override { return {"SysFuncts"}; }

		virtual void run() override;
	};
} // namespace ara::step
