// SPDX-FileCopyrightText: 2020 Björn Fiedler <fiedler@sra.uni-hannover.de>
// SPDX-FileCopyrightText: 2022 Gerion Entrup <entrup@sra.uni-hannover.de>
//
// SPDX-License-Identifier: GPL-3.0-or-later

// vim: set noet ts=4 sw=4:

#pragma once

#include "step.h"

#include <graph.h>

namespace ara::step {
	class SVFTransformation : public ConfStep<SVFTransformation> {
	  private:
		using ConfStep<SVFTransformation>::ConfStep;

	  public:
		static std::string get_name() { return "SVFTransformation"; }
		static std::string get_description();
		virtual std::vector<std::string> get_single_dependencies() override { return {"RemoveSysfuncBody"}; }

		virtual void run() override;
	};
} // namespace ara::step
