#pragma once

#include <string>
#include <tuple>
#include <utility>
#include <vector>
#include <cassert>
#include <sstream>

#include "Python.h"

namespace ara::option {
	template<typename T>
	class RawType {
		public:
		typedef T type;

		protected:
		bool valid = false;
		type value;

		RawType() : step_name("") {}
		virtual ~RawType() {}

		PyObject* get_scoped_object(PyObject* config, std::string name) {
			assert(step_name != "");
			PyObject* ret;
			ret = PyDict_GetItemString(config, "_per_step_config");
			assert(ret);
			ret = PyDict_GetItemString(ret, step_name.c_str());
			if (ret) {
				ret = PyDict_GetItemString(ret, name.c_str());
				if (ret) {
					return ret;
				}
			}
			return PyDict_GetItemString(config, name.c_str());
		}

		private:
		std::string step_name;

		public:

		virtual void from_pointer(PyObject*, std::string) {};

		void check(PyObject* obj, std::string name) {
			PyObject* scoped_obj = get_scoped_object(obj, name);
			this->from_pointer(scoped_obj, name);
		}

		void set_step_name(std::string step_name) { this->step_name = step_name; }

		std::pair<type, bool> get() {
			return std::make_pair(value, valid);
		}
	};

	struct Integer : public RawType<int64_t> {
		virtual void from_pointer(PyObject* obj, std::string name) override;
		using RawType<int64_t>::RawType;
	};

	struct Float : public RawType<double> {
		virtual void from_pointer(PyObject* obj, std::string name) override;
		using RawType<double>::RawType;
	};

	struct Bool : public RawType<bool> {
		virtual void from_pointer(PyObject* obj, std::string name) override;
		using RawType<bool>::RawType;
	};

	struct String : public RawType<std::string> {
		virtual void from_pointer(PyObject* obj, std::string name) override;
		using RawType<std::string>::RawType;
	};

	template <typename T> struct allowed_in_range          { static const bool value = false; };
	template <>           struct allowed_in_range<Integer> { static const bool value = true; };
	template <>           struct allowed_in_range<Float>   { static const bool value = true; };

	template<class T>
	class Range : public RawType<typename T::type> {
		static_assert(allowed_in_range<T>::value, "Range of this type not allowed to be constructed.");

		typename T::type low;
		typename T::type high;

		public:
		Range(typename T::type low, typename T::type high) : RawType<typename T::type>(), low(low), high(high) {}

		void check(PyObject* obj, std::string name) {
			T cont;
			cont.check(obj, name);

			auto ret = cont.get();
			this->value = ret.first;

			if (!ret.second) {
				this->valid = false;
				return;
			}

			if (this->value < low || this->value > high) {
				std::stringstream ss;
				ss << name << ": Range argument " << this->value << "has to be between " << low << " and " << high << "!" << std::flush;
				throw std::invalid_argument(ss.str());
			}

			this->valid = true;
		}
	};

	template <typename T> struct allowed_in_list          { static const bool value = false; };
	template <>           struct allowed_in_list<Integer> { static const bool value = true; };
	template <>           struct allowed_in_list<Float>   { static const bool value = true; };
	template <>           struct allowed_in_list<String>  { static const bool value = true; };

	template<class T>
	class List : public RawType<std::vector<typename T::type>> {
		static_assert(allowed_in_list<T>::value, "List of this type not allowed to be constructed.");

		public:
		using RawType<std::vector<typename T::type>>::RawType;

		void check(PyObject* obj, std::string name) {
			PyObject* scoped_obj = this->get_scoped_object(obj, name);

			if (!scoped_obj) {
				this->valid = false;
				return;
			}

			if (!PyList_Check(scoped_obj)) {
				std::stringstream ss;
				ss << name << ": Must be a list" << std::flush;
				throw std::invalid_argument(ss.str());
			}

			for (Py_ssize_t i = 0; i < PyList_Size(scoped_obj); ++i) {
				T cont;
				cont.from_pointer(PyList_GetItem(scoped_obj, i), name);
				auto ret = cont.get();

				if (!ret.second) {
					this->valid = false;
					return;
				}
				this->value.emplace_back(ret.first);
			}
			this->valid = true;
		}
	};

	template <std::size_t N>
	class Choice : public RawType<typename String::type> {
		int64_t index;
		std::array<String::type, N> choices;

		public:
		Choice(std::array<String::type, N> choices) : RawType<typename String::type>(), choices(choices) {}

		void check(PyObject* obj, std::string name) {
			String cont;
			cont.check(obj, name);

			auto ret = cont.get();
			this->value = ret.first;

			if (!ret.second) {
				this->valid = false;
				return;
			}

			unsigned found_index = 0;
			for (typename String::type& choice : choices) {
				if (this->value == choice) {
					break;
				}
				found_index++;
			}
			if (found_index == choices.size()) {
				std::stringstream ss;
				ss << name << ": Value " << this->value << " is not in the list of possible choices." << std::flush;
				throw std::invalid_argument(ss.str());
			}

			this->valid = true;
		}

		/**
		 * Return the Index of the matching choice.
		 * Can be used to performance critical code..
		 */
		int64_t getIndex() { return index; }
	};

	template<class...T2, int N = sizeof...(T2)>
	constexpr auto makeChoice(T2... args) -> Choice<N> {
		std::array<String::type, N> arr = { args... };
		return Choice<N>(std::move(arr));
	}


	/**
	 * Description object for options
	 */
	struct Option {
		const std::string name;
		const std::string help;

		Option(std::string name, std::string help) : name(name), help(help) {}
		Option() = default;

		virtual ~Option() = default;

		/**
		 * check in global config dict for this option.
		 */
		virtual void check(PyObject*) = 0;

		virtual void set_step_name(std::string step_name) = 0;
	};

	/**
	 * A Typed Option, aka an option with option which also stores its type.
	 */
	template<class T>
	class TOption : public Option {
		private:
		T ty;
		bool global;


		public:
		TOption(std::string name, std::string help, T ty = T(), bool global = false) : Option(name, help), ty(ty), global(global) {}

		virtual void set_step_name(std::string step_name) override {
			ty.set_step_name(step_name);
		}

		virtual void check(PyObject* obj) override {
			ty.check(obj, name);
		}

		/**
		 * get value of option.
		 */
		std::pair<typename T::type, bool> get() {
			ty.get();
		}
	};
} // namespace ara::option
