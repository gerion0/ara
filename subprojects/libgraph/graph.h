// vim: set noet ts=4 sw=4:

#ifndef GRAPH_H
#define GRAPH_H

#include <any>
#include <functional>
#include <list>
#include <string>
#include <tuple>
#include <typeinfo>
#include <memory>
#include "llvm/IR/Module.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Type.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Function.h"
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/IR/DiagnosticInfo.h>
#include "llvm/Analysis/PostDominators.h"
#include "llvm/IR/Dominators.h"
#include "llvm/Analysis/LoopInfo.h"

#include <iostream>
#include <sstream>
#include <queue>


enum function_definition_type { Task, ISR, Timer, normal };

enum call_definition_type { sys_call, func_call, computation , has_call ,no_call};

enum syscall_definition_type { computate ,create, destroy, reset ,receive, commit ,release ,schedule,activate,enable,disable,take,add,take_out,wait,synchronize,set_priority,resume,suspend,enter_critical,exit_critical,start_scheduler};

enum ISR_type { ISR1, ISR2, basic };

enum timer_type { oneshot, autoreload ,autostart};

enum buffer_type { stream = 0, message = 1 };

enum hook_type { start_up, shut_down, pre_task, post_task, error, failed,idle,stack_overflow,tick,no_hook };

enum timer_action_type {activate_task, set_event, alarm_callback};

enum resource_type {standard, linked, internal,binary_mutex = 1, recursive_mutex = 4 };

enum semaphore_type {   binary_semaphore = 3, counting_semaphore = 2};

enum schedule_type {full, none};

enum event_type {automatic, mask};

enum start_scheduler_relation { before , after , uncertain,not_defined };

enum os_type {OSEK,FreeRTOS};


struct argument_data {  
    std::vector<std::any> any_list;   
    std::vector<llvm::Value*> value_list;
    std::vector<std::vector<llvm::Instruction*>> argument_calles_list;
    bool multiple = false;
};


struct call_data {  
		std::string call_name; // Name des Sycalls
		std::vector<argument_data> arguments;
		llvm::Instruction* call_instruction;
        bool sys_call = false;
};

//bool instruction_before( Instruction *InstA,  Instruction *InstB,DominatorTree *DT);
void get_call_relative_argument(std::any &any_value,llvm::Value* &llvm_value,argument_data argument,std::vector<llvm::Instruction*>*call_references);
void debug_argument(argument_data argument);
bool list_contains_element(std::list<std::size_t>* list, size_t target);
call_data get_syscall_relative_arguments(std::vector<argument_data>* arguments,std::vector<llvm::Instruction*>*call_references,llvm::Instruction* call_instruction_reference,std::string call_name);



namespace OS
{
    class ABB;
};

namespace graph {


	class Graph;
	class Vertex;
	class Edge;
	class OS::ABB;
    
	typedef std::shared_ptr<OS::ABB> shared_abb;
	typedef std::shared_ptr<Vertex> shared_vertex;
	typedef std::shared_ptr<Edge>  shared_edge;


	// Basis Klasse des Graphen
	class Graph {

		private:
			std::list<std::shared_ptr<Vertex>> vertices; // std::liste aller Vertexes des Graphen
			std::list<std::shared_ptr<Edge>> edges;      // std::liste aller Edges des Graphen
			
			std::shared_ptr<llvm::Module> llvm_module;
			

            os_type type;
                
		public:
                
			//Graph(std::shared_ptr<llvm::Module>module);
	
			Graph();
	
			void load_llvm_module(std::string file);
			void set_llvm_module(std::shared_ptr<llvm::Module> module);
                
			std::shared_ptr<llvm::Module> get_llvm_module();
                
			void set_vertex(shared_vertex vertex); // vertex.clone(); innerhalb der set Methode um Objekt für die Klasse Graph zu speichern
			void set_edge(shared_edge edge); // edge.clone(); innerhalb der set Methode um Objekt für die Klasse Graph zu speichern
			
			shared_vertex create_vertex();
			shared_edge create_edge();
					
			std::list<shared_vertex>get_type_vertices(size_t type_info); // gebe alle Vertexes eines Types (Task, ISR, etc.) zurück
			shared_vertex get_vertex(size_t seed);     // gebe Vertex mit dem entsprechenden hashValue zurück
			shared_edge get_edge(size_t seed);     // gebe Edge mit dem entsprechenden hashValue zurück
			
			shared_vertex get_vertex(std::string name);     // gebe Edge mit dem
			
			std::list<shared_vertex> get_vertices();  // gebe alle Vertexes des Graphen zurück
                
			std::list<shared_edge> get_edges();  // gebe alle Edges des Graphen zurück

			bool remove_vertex(shared_vertex vertex); // löschen den Vertex mit dem Namen und automatisch alle Knoten des Vertexes
			
			bool remove_vertex(size_t seed);
												// aus dem Graphen
			bool remove_edge(shared_edge *edge); // löschen den Vertex mit dem Namen und automatisch alle Knoten des Vertexes aus dem Graphen
                
			bool contain_vertex(shared_vertex vertex);
			bool contain_edge(shared_edge edge);
			
			void print_information();
            
            os_type get_os_type(){return  this->type;};
            
            void set_os_type(os_type type){this->type = type;};
			
			
			~Graph();
                
	};


	// Basis Klasse für alle Vertexes
	class Vertex {

	  protected:
          
          
		Graph *graph; // Referenz zum Graphen, in der der Vertex gespeichert ist

		
		bool static_create = false;
		bool multiple_create = false;
        
		std::size_t vertex_type;
		std::string name; // spezifischer Name des Vertexes
		std::size_t seed; // für jedes Element spezifischer hashValue

		std::list<shared_edge> outgoing_edges; // std::liste mit allen ausgehenden Kanten zu anderen Vertexes
		std::list<shared_edge> ingoing_edges;  // std::liste mit allen eingehenden Kanten von anderen Vertexes

		std::list<shared_vertex> outgoing_vertices; // std::liste mit allen ausgehenden Vertexes zu anderen Vertexes
		std::list<shared_vertex> ingoing_vertices;  // std::liste mit allen eingehenden Vertexes von anderen Vertexes

		std::string handler_name;
		
		bool start_scheduler_creation_flag;
        
        
					
	  public:
              /*
		// Discriminator for LLVM-style RTTI (dyn_cast<> et al.)
		enum VertexKind {
			Function,
			ISR,
			Timer,
			Task,
			Queue,
			EventGroups,
			Semaphore,
			Buffer,
			QueueSet

		};
		const VertexKind Kind;
		*/
		
		virtual void print_information(){
			
		};
                
		Vertex(Graph *graph,std::string name); // Constructor
    
		
		void set_start_scheduler_creation_flag(bool flag);
		bool get_start_scheduler_creation_flag();
		
		void set_type(std::size_t type);
		std::size_t get_type();
                
		std::string get_name(); // gebe Namen des Vertexes zurück
		std::size_t get_seed(); // gebe den Hash des Vertexes zurück

		//VertexKind getKind(); // LLVM-style RTTI const {return Kind}

		void set_handler_name(std::string handler_name);
		std::string get_handler_name();
		bool set_outgoing_edge(shared_edge edge);
		bool set_ingoing_edge(shared_edge edge);

		bool set_outgoing_vertex(shared_vertex vertex);
		bool set_ingoing_vertex(shared_vertex vertex);

		bool remove_edge(shared_edge edge);
		bool remove_vertex(shared_vertex vertex);
                
		Graph* get_graph();

		std::list<shared_vertex> get_specific_connected_vertices(size_t type_info); // get elements from graph with specific type

		std::list<shared_vertex> get_vertex_chain(shared_vertex target_vertex); // Methode, die die Kette der Elemente vom Start bis zum Ziel Vertex zurück gibt,
		                     // interagieren die Betriebssystemabstrakionen nicht miteinader gebe nullptr zurück
		std::list<shared_vertex>
		get_connected_vertices();                // Methode, die die mit diesem Knoten verbundenen Vertexes zurückgibt
		std::list<shared_edge> get_connected_edges(); // Methode, die die mit diesem Knoten verbundenen Edges zurückgibt
		std::list<shared_vertex> get_ingoing_vertices(); // Methode, die die mit diesem Knoten eingehenden Vertexes
		                                            // zurückgibt
		std::list<shared_edge> get_ingoing_edges(); // Methode, die die mit diesem Knoten eingehenden Edges zurückgibt
		std::list<shared_vertex>
		get_outgoing_vertices();                // Methode, die die mit diesem Knoten ausgehenden Vertexes zurückgibt
		std::list<shared_edge> get_outgoing_edges(); // Methode, die die mit diesem Knoten ausgehenden Edges zurückgibt
		std::list<shared_edge>get_direct_edge(shared_vertex vertex); // Methode, die direkte Kante zwischen Start und Ziel Vertex zurückgibt,
		                                   // falls keine vorhanden nullptr
        
        void set_static_create(bool create){
            this->static_create = create;
        }

        bool get_static_create(){
            return this->static_create;
        }
        
        void set_multiple_create(bool create){
            this->multiple_create = create;
        }

        bool get_multiple_create(){
            return this->multiple_create;
        }
	};

	
	// Klasse Edge verbindet zwei Betriebssystemabstraktionen über einen Syscall/Call mit entsprechenden Argumenten
	// Da jeder Edge der Start und Ziel Vertex zugeordnet ist, kann der Graph durchlaufen werden
	class Edge {

	  private:
		std::string name;
		Graph *graph;          // Referenz zum Graphen, in der der Vertex gespeichert ist
		std::size_t seed;      // für jedes Element spezifischer hashValue
		shared_vertex start_vertex;  // Entsprechende Set- und Get-Methoden
		shared_vertex target_vertex; // Entsprechende Set- und Get-Methoden
		bool is_syscall;       // Flag, ob Edge ein Syscall ist
		std::list<argument_data> arguments;
		shared_abb atomic_basic_block_reference;
        llvm::Instruction* instruction_reference;
        
		call_data call;

	  public:
		
    		
		Edge();
		Edge(Graph *graph, std::string name, shared_vertex start, shared_vertex target,shared_abb atomic_basic_block_reference);

		std::string get_name(); // gebe Namen des Vertexes zurück
		std::size_t get_seed(); // gebe den Hash des Vertexes zurück

		bool set_start_vertex(shared_vertex vertex);
		bool set_target_vertex(shared_vertex vertex);
		shared_vertex get_start_vertex();
		shared_vertex get_target_vertex();
        
        void set_call(call_data *call);
        
        void set_instruction_reference(llvm::Instruction* reference);
		llvm::Instruction* get_instruction_reference();
        
        shared_abb get_abb_reference();
        
		void set_syscall(bool syscall);
		bool is_sycall();

		std::list<argument_data>* get_arguments();
		void set_arguments(std::list<argument_data> arguments);
		void set_argument(argument_data data);
        void set_specific_call(call_data* call);
        call_data get_specific_call();
	};
} // namespace graph




namespace OS {

	class ABB;
	class Task;
	class ISR;
	class QueueSet;
	class Function;
	class Resource;
	class Message;
	class Event;
	class Counter;
	class RTOS;
	
	typedef std::shared_ptr<ABB> shared_abb;
	typedef std::shared_ptr<Function> shared_function;
	typedef std::shared_ptr<Task> shared_task;
	typedef std::shared_ptr<ISR> shared_isr;
	typedef std::shared_ptr<QueueSet> shared_queueset;
	typedef std::shared_ptr<Resource> shared_resource;
	typedef std::shared_ptr<Message> shared_message;
	typedef std::shared_ptr<Event> shared_event;
	typedef std::shared_ptr<Counter> shared_counter;

	
		
	typedef std::shared_ptr<RTOS> shared_os;
	
	class RTOS : public graph::Vertex {

        public:
            bool preemption = false;
            bool time_slicing = false;
            bool should_yield = false;
            
            unsigned int tick_rate_hz = 0;
            unsigned int cpu_clock_hz = 0;
            
            bool idle_hook = false;
            bool tick_hook = false;
            bool malloc_failed_hook = false;
            bool daemon_task_startup_hook = false;

            bool support_static_allocation = false;
            bool support_dynamic_allocation = false;
            int heap_type = -1;
            unsigned long total_heap_size = 0;
            
            bool startup_hook = false;
            bool error_hook = false;       
            bool shutdown_hook = false;
            bool pretask_hook = false;
            bool posttask_hook = false;
            
            void enable_startup_hook(bool flag) {startup_hook = flag ;};
            void enable_error_hook (bool flag) {error_hook = flag; };    
            void enable_shutdown_hook(bool flag) {shutdown_hook = flag; };
            void enable_pretask_hook (bool flag) {pretask_hook = flag; };
            void enable_posttask_hook (bool flag) {posttask_hook = flag; };
            
            
            bool support_16_bit_ticks = false;
            bool support_coroutines = false;
            bool support_queue_sets = false;
            bool support_counting_semaphores = false;
            bool support_recursive_mutexes = false;
            bool support_mutexes = false;
            bool support_task_notification = false;
        
            
            std::string appmode;
            
            
            unsigned long max_coroutine_priorities = 0;
            
            bool scheduler_resource = false;

            RTOS(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
                std::hash<std::string> hash_fn;
                this->seed = hash_fn(name +  typeid(RTOS).name());
                this->vertex_type =  typeid(RTOS).hash_code();
                this->handler_name = "RTOS";
            }
	};
	
	
	
	
	// Einfache Funktion innerhalb der Applikation
	class Function : public graph::Vertex {
		
	  private:
		
		bool syscall_flag = false;
		
		//TODO make a list of this
		graph::shared_vertex definition_element = nullptr;
		
		std::string function_name;       // name der Funktion
		std::list<llvm::Type*> argument_types; // Argumente des Functionsaufrufes
		llvm::Type* return_type;

		std::list<OS::shared_abb> atomic_basic_blocks;       // Liste der AtomicBasicBlocks, die die Funktion definieren
		std::list<OS::shared_task> referenced_tasks;     // Liste aller Task, die diese Function aufrufen
		std::list<OS::ISR *> referenced_ISRs;
		function_definition_type definition; // information, ob task ,isr, timer durch die Funktion definiert wird

		bool contains_critical_section = false;

		llvm::BasicBlock *start_critical_section_block; //  LLVM BasicBlock reference
		llvm::BasicBlock *end_critical_section_block;   //  LLVM BasicBlock reference

		llvm::Function *LLVM_function_reference; //*Referenz zum LLVM Function Object LLVM:Function -> Dadurch sind die
		                                         //sind auch die LLVM:BasicBlocks erreichbar und iterierbar*/
		
		hook_type hook = no_hook;
		
		shared_abb entry_abb = nullptr;
		shared_abb exit_abb = nullptr;
        
        llvm::DominatorTree dominator_tree = llvm::DominatorTree();
        llvm::PostDominatorTree  postdominator_tree = llvm::PostDominatorTree();
        llvm::LoopInfoBase<llvm::BasicBlock, llvm::Loop> loop_info_base;
                                                            
	  public:
                              
              
		void print_information();
		
		static bool classof(const Vertex *v); // LLVM RTTI class of Methode
                
                
		Function(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
			this->function_name = name;
			std::hash<std::string> hash_fn;
			this->seed = hash_fn(name +  typeid(Function).name());
			this->vertex_type =  typeid(Function).hash_code();
			
		}
		
		void has_syscall(bool flag);
		
		bool has_syscall();
		
		void set_entry_abb(shared_abb abb);
		shared_abb get_exit_abb();
		void set_exit_abb(shared_abb abb);
		
		shared_abb get_entry_abb();

		void set_definition(function_definition_type type);
		function_definition_type get_definition();
		
		llvm::DominatorTree* get_dominator_tree();
        llvm::PostDominatorTree* get_postdominator_tree();
        
        void initialize_dominator_tree(llvm::Function* function);

        void initialize_postdominator_tree(llvm::Function *function);
        
       
        llvm::LoopInfoBase<llvm::BasicBlock, llvm::Loop>* get_loop_info_base();
        
        
        
		bool set_definition_vertex(graph::shared_vertex vertex);
		graph::shared_vertex get_definition_vertex();
                
		//Funktionen zurück, die diese Funktion benutzen
		bool set_used_function(OS::Function *function); // Setze Funktion in std::liste aller Funktionen, die diese Funktion benutzen


		bool set_start_critical_section_block(llvm::BasicBlock *basic_block);
		bool set_end_critical_section_block(llvm::BasicBlock *basic_block);

		llvm::BasicBlock *get_start_critical_section_block();
		llvm::BasicBlock *get_end_critical_section_block();

		bool has_critical_section();
		void set_critical_section(bool flag);
                
		bool set_llvm_reference(llvm::Function *function);
		llvm::Function *get_llvm_reference();

		void set_atomic_basic_block(OS::shared_abb atomic_basic_block);
        void set_atomic_basic_blocks(std::list<OS::shared_abb> * atomic_basic_blocks);
		//std::list<graph::shared_vertex> get_atomic_basic_blocks();
		
		std::list<OS::shared_abb> get_atomic_basic_blocks();
		
		std::list<shared_task> get_referenced_tasks();

		bool set_referenced_task(shared_task task);

		bool set_called_function(shared_function function,shared_abb abb );
		std::vector<OS::shared_function> get_called_functions();
        std::vector<OS::shared_function> get_calling_functions();
		
		void set_function_name(std::string name);
		std::string get_function_name();
                
		void set_hook_type(hook_type hook){
            this->hook = hook;
        };
        
		std::list<llvm::Type*> get_argument_types();
		void set_argument_type(llvm::Type* argument); // Setze Argument des SystemCalls in Argumentenliste
                
		void set_return_type(llvm::Type* argument); 
		llvm::Type * get_return_type();
		
		bool has_single_successor();
		
		bool remove_abb(size_t seed);
	};

	// Klasse AtomicBasicBlock
	class ABB: public graph::Vertex  {

	  private:
          
        start_scheduler_relation start_scheduler_relative_position = after;
        
		call_definition_type    abb_type; // Information, welcher Syscall Typ, bzw. ob Computation Typ vorliegt (Computation, generate Task,
		          // generate Queue, ....; jeder Typ hat einen anderen integer Wert)
		
		syscall_definition_type abb_syscall_type;
		std::list<shared_abb> successors;   // AtomicBasicBlocks die dem BasicBlock folgen
		std::list<shared_abb> predecessors;  // AtomicBasicBlocks die dem BasicBlock vorhergehen
		shared_function parent_function; // Zeiger auf Function, die den BasicBlock enthält
		
		
		std::vector<llvm::BasicBlock *> basic_blocks;

        /*
		std::list<std::string> call_names; // Name des Sycalls
		
		std::string syscall_name;
		std::vector<llvm::Instruction*> call_instruction_references;
		std::list<std::list<argument_data>> arguments;
        std::list<argument_data>syscall_arguments;
        llvm::Instruction* syscall_instruction_reference = nullptr;
        */
        
        //the expected instance types which can be addressed with the syscall
		std::list<std::size_t>  call_target_instances;
		
		
		llvm::BasicBlock* entry;
		llvm::BasicBlock* exit;
		

        //std::vector<call_data> calls;
        call_data call;
		
        
		bool critical_section; // flag, ob AtomicBasicBlock in einer ḱritischen Sektion liegt
		
		size_t syscall_handler_index;
        
        bool in_loop = false;

	  public:
              		
		void print_information();
		
		ABB(graph::Graph *graph,shared_function function, std::string name) : graph::Vertex(graph,name){
			parent_function = function;
			std::hash<std::string> hash_fn;
			this->seed = hash_fn(name +  typeid(ABB).name());
			this->abb_type = no_call;
			this->vertex_type = typeid(ABB).hash_code();
		}
		
		void set_handler_argument_index(size_t index);
		size_t get_handler_argument_index();
		
		//std::vector<llvm::Instruction*> get_call_instruction_references();
		llvm::Instruction* get_call_instruction_reference();
		
        void set_start_scheduler_relation(start_scheduler_relation relation);
        start_scheduler_relation get_start_scheduler_relation( );
		
		llvm::Instruction* get_syscall_instruction_reference();
		
		syscall_definition_type get_syscall_type();
		void set_syscall_type(syscall_definition_type type);
		
		call_definition_type get_call_type();
		void set_call_type(call_definition_type type);

		std::list<std::size_t>*  get_call_target_instances();
		void set_call_target_instance(size_t target_instance);
		
		
        void set_call(call_data* call);
        
        call_data get_call();
        
		//std::vector<std::string> get_call_names();
        std::string get_call_name();
		std::string get_syscall_name();
		bool set_syscall_name(std::string call_name);
        
		void expend_call_sites(shared_abb abb);
		llvm::BasicBlock* get_exit_bb();
		llvm::BasicBlock* get_entry_bb();
		
		void set_exit_bb(llvm::BasicBlock* bb);
		void set_entry_bb(llvm::BasicBlock* bb);
		
		
		void adapt_exit_bb(shared_abb abb);
		

		bool set_parent_function(shared_function function);
		shared_function get_parent_function();
				
		OS::shared_function get_called_function();
        
        
		void set_called_function(OS::shared_function, llvm::Instruction* instr);
		
		bool is_critical();
		void set_critical(bool critical);

		//std::list<std::tuple<std::any,llvm::Type*>> get_arguments_tmp();
		std::vector<argument_data> get_arguments();
		
		
		std::vector<argument_data> get_syscall_arguments();
		
		
		bool set_ABB_successor(shared_abb basicblock);   // Speicher Referenz auf Nachfolger des BasicBlocks
		bool set_ABB_predecessor(shared_abb basicblock); // Speicher Referenz auf Vorgänger des BasicBlocks
		std::list<shared_abb> get_ABB_successors();      // Gebe Referenz auf Nachfolger zurück
		shared_abb get_single_ABB_successor();
		std::list<shared_abb> get_ABB_predecessors();    // Gebe Referenz auf Vorgänger zurück

		bool set_BasicBlock(llvm::BasicBlock* basic_block);
		std::vector<llvm::BasicBlock*>* get_BasicBlocks();
		//std::list<size_t> get_expected_syscall_argument_types();
        
 		std::list<std::list<size_t>> get_call_argument_types();
		
		void remove_successor(shared_abb abb);
		void remove_predecessor(shared_abb abb);
		
		bool convert_call_to_syscall(std::string name);
		bool append_basic_blocks(shared_abb abb);
		
		bool has_single_successor();
		bool is_mergeable();
		void merge_call_sites(shared_abb abb);
		
		shared_abb get_dominator();
		
		shared_abb get_postdominator();
        
        void set_loop_information(bool flag);
        
        bool get_loop_information();
        
	};

	// Bei Betriebssystem Abstraktionen wurden für die Attribute, die get- und set-Methoden ausgelassen und ein direkter
	// Zugriff erlaubt. Vielmehr wird der Zugriff auf interne Listen durch Methoden ermöglicht.

	class TaskGroup : public graph::Vertex {

	  private:
		std::list<OS::shared_task> task_group;

	  public:
		
		TaskGroup(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
			this->vertex_type = typeid(TaskGroup).hash_code();
			std::hash<std::string> hash_fn;
			this->seed = hash_fn(name +  typeid(TaskGroup).name());
		} 
		
	
		
		void print_information(){	
		};
		
		std::string group_name;
		
		bool set_task_in_group(OS::shared_task task);
		bool remove_task_in_group(OS::shared_task task);
		std::list<OS::shared_task> get_tasks_in_group();
	};

	class Task : public graph::Vertex {
	
	private:
		
		OS::shared_function definition_function;
		TaskGroup *task_group;
		
		std::list<shared_resource> resources;
		std::list<shared_event> events;
		std::list<shared_message> messages;
		std::list<std::string> app_modes;
	
		int stacksize;
		int priority;
		
		// FreeRTOS attributes
		llvm::Type* parameter;
		bool gatekeeper;

		// OSEK attributes
		bool autostart;	// Information if Task is activated during system start or or application mode
		unsigned int activation;
		schedule_type scheduler; //NON/FULL defines preemptability of task
		
		bool constant_priority = true;
		
	public:
		
		Task(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
			this->vertex_type = typeid(Task).hash_code();
			std::hash<std::string> hash_fn;
			this->seed = hash_fn(name +  typeid(Task).name());
			//std::cout << "type: " << this->vertex_type  << std::endl;
		}
		
		
		void print_information(){
		
		};
		

		
		
		bool set_task_group(std::string taskgroup); //name of TaskGroup
		bool set_definition_function(std::string function_name);
        
        shared_function get_definition_function();

		void set_priority(unsigned long priority);
        unsigned long  get_priority();
		void set_stacksize(unsigned long priority);
		bool set_scheduler(std::string scheduler);
		void set_activation(unsigned long activation);
		void set_autostart(bool autostart);
		void set_appmode(std::string app_mode);
		bool set_resource_reference(std::string resource);
		bool set_event_reference(std::string event);
		bool set_message_reference(std::string message);
		void set_constant_priority(bool is_constant);
		bool has_constant_priority();

	};


	class ISR : public graph::Vertex {

		OS::shared_function definition_function;
		
		
		//OSEK attributes
		int category;			// OSEK just values 0 and 1 are allowed
		int stacksize;
		
		std::list<shared_resource> resources;
		std::list<shared_message> messages;
		
		//FreeRTOS attributes
		std::string interrupt_source;
		int priority;
		
	  public:

		ISR(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
			this->vertex_type = typeid(ISR).hash_code();
			std::hash<std::string> hash_fn;
			this->seed = hash_fn(name +  typeid(ISR).name());
		}
		
		void print_information(){

		};

		bool set_category(int category);
		bool set_message_reference(std::string);
		bool set_resource_reference(std::string);
		bool set_definition_function(std::string definition_function_name);
        shared_function get_definition_function();
		static bool classof(const Vertex *S);
	};

	class QueueSet : public graph::Vertex {

	  private:
		  

			unsigned long length;
		
			std::vector<graph::shared_vertex> queueset_elements; //  Queues, Semaphores

	  public:
	  
			QueueSet(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(QueueSet).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(QueueSet).name());
			}

			void set_queue_element(graph::shared_vertex element);
			bool member_of_queueset(graph::shared_vertex element);
			bool remove_from_queueset(graph::shared_vertex element);

			std::vector<graph::shared_vertex>* get_queueset_elements(); // gebe alle Elemente der Queueset zurück
		

		
			void set_length (unsigned long length);

	};

	class Queue : public graph::Vertex {
		
		private:
			
			OS::shared_queueset queueset_reference; // Referenz zur Queueset

		
			int length;              // Länger der Queue
			int item_size;
				
		public:
			
			Queue(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(Queue).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(Queue).name());
			}
			void print_information(){
			
			};
			
		
			
			
			unsigned long get_item_size();
			void set_item_size(unsigned long size);
			
			unsigned long get_length();
			void set_length(unsigned long size);
			
			bool set_queueset_reference(shared_queueset);
			shared_queueset get_queueset_reference();
			std::list<graph::shared_vertex> get_accessed_elements(); // gebe ISR/Task zurück, die mit der Queue interagieren

			static bool classof(const Vertex *S);
	};


	class Event : public graph::Vertex {

	  private:
          
        std::list<OS::shared_task> task_reference;
        unsigned long  event_mask;
        unsigned int id;
        event_type mask_type;

		//std::list<long> set_bits;     // Auflisten aller gesetzen Bits des Event durch Funktionen
		std::list<long> cleared_bits; // Auflisten aller gelöschten Bits des Event durch Funktionen, gelöschte Bits
		                             // müssen auch wieder gesetzt werden
		std::list<graph::shared_vertex > synchronized_vertices; // Alle Vertexes die durch den EventGroupSynchronized Aufruf synchronisiert werden
		
	  public:
		
		Event(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(Event).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(Event).name());
		}
		
		void print_information(){
			
		};
			
		
		bool wait_for_all_bits;
		bool wait_for_any_bit;

		bool set_bits(long bit);
		bool set_cleared_bits(long bit);

		bool remove_bits(long bit);
		bool remove_cleared_bits(long bit);

		bool is_set_bits(long bit);
		bool is_cleared_bits(long bit);

        
        bool set_task_reference(OS::shared_task task);
        std::list<OS::shared_task> get_task_references();
        void set_event_mask(unsigned long  mask);
        void set_event_mask_auto();
        void set_id(unsigned int id);
        
	};
    

	class Buffer : public graph::Vertex {
	  
		private:
			
			buffer_type type; // enum buffer_type {stream, message}
			graph::shared_vertex reader;   // Buffer sind als single reader und single writer objekte gedacht
			graph::shared_vertex writer;
			unsigned long buffer_size;
			unsigned long trigger_level; // Anzahl an Bytesm, die in buffer liegen müssen, bevor der Task den block status verlassen
							// kann

		public:
			
			Buffer(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(Buffer).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(Buffer).name());
		
			};
			
			void set_trigger_level(unsigned long level);
			void set_buffer_size(unsigned long size);
			void set_buffer_type(buffer_type type);
		
		
			
			void print_information(){
			
			};

	};
    
    
    class Semaphore :public graph::Vertex{
		
		private:
            
            semaphore_type type; // enum semaphore_type {binary, counting, mutex, recursive_mutex}
		
			unsigned long max_count;
			unsigned long initial_count;
            
		
		public:
			Semaphore(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(Semaphore).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(Semaphore).name());
				//std::cerr << "name subclass: " << name << std::endl;
			};
			
            void set_semaphore_type(semaphore_type type);
			semaphore_type get_semaphore_type();
			
			void set_max_count(unsigned long count);
			unsigned long get_max_count();
			
			void set_initial_count(unsigned long count);
			unsigned long get_initial_count();
	};
	
	
	class Resource :public graph::Vertex{
		
		private:
            
            resource_type type; // enum semaphore_type {binary, counting, mutex, recursive_mutex}
		
			unsigned long max_count;
			unsigned long initial_count;
            
			std::list<OS::shared_task> tasks;
			std::list<OS::shared_isr> irs;
			std::list<OS::shared_resource> resources;
			
		public:
			Resource(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(Resource).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(Resource).name());
				//std::cerr << "name subclass: " << name << std::endl;
			};
			bool set_task_reference(OS::shared_task task);
			std::list<OS::shared_task> get_task_references();
			
			bool set_isr_reference(OS::shared_isr isr);
			std::list<OS::shared_isr> get_isr_references();
			
			bool set_linked_resource(OS::shared_resource resource);
			std::list<OS::shared_resource> get_linked_resources();
			
			bool set_resource_property(std::string type, std::string linked_resource);
            
            void set_resource_type(resource_type type);
			resource_type get_resource_type();
			
			void set_max_count(unsigned long count);
			unsigned long get_max_count();
			
			void set_initial_count(unsigned long count);
			unsigned long get_initial_count();
	};
	
    
    
    
	class Counter :public graph::Vertex{
		
			unsigned long max_allowed_value;
			unsigned long ticks_per_base;
			unsigned long min_cycle;
			
		public:
			
			Counter(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
				this->vertex_type = typeid(Counter).hash_code();
				std::hash<std::string> hash_fn;
				this->seed = hash_fn(name +  typeid(Counter).name());
				//std::cerr << "name subclass: " << name << std::endl;
			};
			
			
			void print_information(){
				
			};
			
			void set_max_allowed_value(unsigned long max_allowedvalue);
			void set_ticks_per_base(unsigned long ticks);
			void set_min_cycle(unsigned long min_cycle); 
	};
	
    
    
    
    
    class Timer : public graph::Vertex {

        private:
            
            OS::shared_task referenced_task;
            OS::shared_event referenced_event;
            OS::shared_counter referenced_counter;
            OS::shared_function callback_function;
                           
            timer_action_type reaction;
            

            
            std::list<std::string> appmodes;
            
            unsigned int alarm_time;
            unsigned int cycle_time;
            int periode;     // Periode in Ticks
            timer_type type; // enum timer_type {One_shot_timer, Auto_reload_timer}
            int timer_id; // ID is a void pointer and can be used by the application writer for any purpose. useful when the
                        // same callback function is used by more software timers because it can be used to provide
                        // timer-specific storage.
            
        public:

            Timer(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
                this->vertex_type = typeid(Timer).hash_code();
                std::hash<std::string> hash_fn;
                this->seed = hash_fn(name +  typeid(Timer).name());
            }

        
            void print_information(){
                
            };
            
            void set_timer_type(timer_type type);
            timer_type get_timer_type();
            void set_timer_id(unsigned long timer_id);
            void set_periode(unsigned long period);
            
            unsigned long get_timer_id();
            unsigned long get_periode();
            
            bool set_callback_function(std::string definition_function_name);
            shared_function get_callback_function();
            
            bool set_task_reference(std::string task);
            OS::shared_task get_task_reference();
            
            bool set_counter_reference(std::string counter);
            OS::shared_counter get_counter_reference();
            
            
            bool set_event_reference(std::string event);
                        
            void set_alarm_time(unsigned int alarm_time);
            void set_cycle_time(unsigned int cycle_time);
            
            void set_appmode(std::string appmode);
            
            void set_timer_action_type(timer_action_type type);
            timer_action_type get_timer_action_type();

	};
    
    class CoRoutine : public graph::Vertex {

        private:
            
            unsigned int id;
            unsigned int priority;
            OS::shared_function definition_function;
            
            
        public:

            CoRoutine(graph::Graph *graph,std::string name) : graph::Vertex(graph,name){
                this->vertex_type = typeid(CoRoutine).hash_code();
                std::hash<std::string> hash_fn;
                this->seed = hash_fn(name +  typeid(CoRoutine).name());
            }

        
            void print_information(){
                
            };
            

            bool set_definition_function(std::string definition_function_name);
            shared_function get_definition_function();
            
     		void set_priority(unsigned long priority);
            unsigned long  get_priority();
            
            void set_id(unsigned long priority);
            unsigned long  get_id();


	};
	
	
	

} // namespace OS

#endif // GRAPH_H
