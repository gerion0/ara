from ..syscall_generic import GenericSystemCalls
from ..elements import (DataObjectArray, DataObject, Function, FunctionCall,
                       Statement, Include, CPPStatement,
                       FunctionDeclaration)
from ara.os.freertos import Task, Queue, Mutex

class SystemCallsInstantiationStatic(GenericSystemCalls):


    def generate_data_objects(self):
        '''generate the data objects for tasks and queues'''
        #TODO: Stack Speicher global
        #TODO: TCB Speicher global
        #TODO: QueueStorage
        #TODO: Queue Verwaltungsstruktur
        task_list = [self.ara_graph.instances.vp.obj[v]
                     for v in self.ara_graph.instances.vertices()
                     if isinstance(self.ara_graph.instances.vp.obj[v], Task)]
        queue_list = [self.ara_graph.instances.vp.obj[v]
                     for v in self.ara_graph.instances.vertices()
                     if isinstance(self.ara_graph.instances.vp.obj[v], Queue)]
        mutex_list = [self.ara_graph.instances.vp.obj[v]
                     for v in self.ara_graph.instances.vertices()
                     if isinstance(self.ara_graph.instances.vp.obj[v], Mutex)]
        self.mark_specialization_depth()
        self.generate_dataobjects_task_stacks(task_list)
        self.generate_data_objects_tcb_mem(task_list)
        self.generate_data_objects_queue_mem(queue_list, 'static')
        self.generate_data_objects_queue_mem(mutex_list, 'static')
        self.generator.source_file.includes.add(Include('queue.h'))

    def mark_specialization_depth(self):
        for v in self.ara_graph.instances.vertices():
            inst = self.ara_graph.instances.vp.obj[v]
            if inst.unique:
                inst.specialization_level = 'static'
            else:
                inst.specialization_level = 'unchanged'
            self._log.debug("mark: %015s (unique: %s, branch: %s, loop: %s) ==> %s",
                            inst.name,
                            inst.unique,
                            inst.branch,
                            inst.loop,
                            inst.specialization_level)



    def generate_dataobjects_task_stacks(self, task_list):
        '''generate the stack space for the tasks'''
        for task in task_list:
            self.arch_rules.specialized_stack(task)

    def generate_data_objects_tcb_mem(self, task_list):
        '''generate the memory for the tcbs'''
        for task in task_list:
            if task.specialization_level == 'unchanged':
                continue
            self.arch_rules.static_unchanged_tcb(task)

    def generate_system_code(self):
        super().generate_system_code()
        task_list = [self.ara_graph.instances.vp.obj[v]
                     for v in self.ara_graph.instances.vertices()
                     if isinstance(self.ara_graph.instances.vp.obj[v], Task)]
        queue_list = [self.ara_graph.instances.vp.obj[v]
                      for v in self.ara_graph.instances.vertices()
                      if isinstance(self.ara_graph.instances.vp.obj[v], Queue)]
        mutex_list = [self.ara_graph.instances.vp.obj[v]
                      for v in self.ara_graph.instances.vertices()
                      if isinstance(self.ara_graph.instances.vp.obj[v], Mutex)]
        all_instances = [self.ara_graph.instances.vp.obj[v]
                         for v in self.ara_graph.instances.vertices()]
        self._log.debug("Instances: %s", len(list(self.ara_graph.instances.vertices())))
        self._log.debug("Tasks: %s", len(task_list))
        self._log.debug("Queues: %s", len(queue_list))
        self._log.debug("Mutexes: %s", len(mutex_list))
        self.mark_init_support(all_instances)
        self.generate_system_code_init_tasks(task_list)
        self.generator.source_file.includes.add(Include('FreeRTOS.h'))
        if len(task_list) or len(queue_list) or len(mutex_list):
            self.generator.ara_step._step_manager.chain_step({'name':'ReplaceSyscallsCreate'})

    def mark_init_support(self, instance_list):
        static_instantiation = any([inst.specialization_level in ['initialized', 'static']
                                    for inst in instance_list])
        dynamic_instantiation = any([inst.specialization_level == 'unchanged'
                                     for inst in instance_list])

        overrides = self.generator.source_files['.freertos_overrides.h'].overrides
        overrides['configSUPPORT_STATIC_ALLOCATION'] = int(
            getattr(overrides, 'configSUPPORT_STATIC_ALLOCATION', False)
            or static_instantiation)
        overrides['configSUPPORT_DYNAMIC_ALLOCATION'] = int(
            getattr(overrides, 'configSUPPORT_DYNAMIC_ALLOCATION', False)
            or dynamic_instantiation)



    def generate_system_code_init_tasks(self, task_list):
        self.generator.source_file.includes.add(Include('task.h'))
        init_func = Function("init_static_system_objects",
                             'void',
                             [],
                             extern_c=True,
        )
        idle_task = None
        for task in task_list:
            self._log.debug("Task: %s", task.name)
            if not task.is_regular:
                if task.name == 'idle_task':
                    idle_task = task
                    self._log.debug("IdleTask: %s", task.name)
                continue

        self.generator.source_file.function_manager.add(init_func)


        if not idle_task:
            self._log.warning("IdleTask not found")
        else:
            mem_f = Function('vApplicationGetIdleTaskMemory',
                                         'void',
                                         ['StaticTask_t **',
                                          'StackType_t **',
                                          'uint32_t *',
                                         ],
                             extern_c=True)
            mem_f.add(Statement(f"*arg0 = &{idle_task.impl.tcb.name}"))
            mem_f.add(Statement(f"*arg1 = &({idle_task.impl.stack.name}[0])"))
            mem_f.add(Statement(f"*arg2 = {idle_task.stack_size}"))
            self.generator.source_file.function_manager.add(mem_f)

        self._init.add(FunctionCall('init_static_system_objects',[]))
