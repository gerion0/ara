# SPDX-FileCopyrightText: 2019 Benedikt Steinmeier
# SPDX-FileCopyrightText: 2020 Manuel Breiden
# SPDX-FileCopyrightText: 2021 Bastian Fuhlenriede
# SPDX-FileCopyrightText: 2022 Björn Fiedler <fiedler@sra.uni-hannover.de>
# SPDX-FileCopyrightText: 2022 Domenik Kuhn
# SPDX-FileCopyrightText: 2022 Gerion Entrup <entrup@sra.uni-hannover.de>
# SPDX-FileCopyrightText: 2022 Jan Neugebauer
#
# SPDX-License-Identifier: GPL-3.0-or-later

if get_option('enable_step_tests')
    test('create-abbs',
        py3_inst,
        args: [files('abb.py'), files('abb.json'), freertos_abb_merge],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    test('dependency-resolving',
        py3_inst,
        args: files('dependency_resolving.py'),
        env: [python_path],
        suite: ['analysis', 'preproc']
    )

    test('dummy-test',
        py3_inst,
        args: [ara_py, 'empty',
               '-v',
               '--os', 'FreeRTOS',
               '--step-settings', files('dummy_settings.json')],
        suite: ['analysis', 'preproc']
    )

    test('equations',
        py3_inst,
        args: [files('equations.py')],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'multisse']
    )

    test('function-pointer',
        py3_inst,
        args: [files('function_pointer.py'), files('function_pointer.json'), freertos_function_pointer],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    test('icfg',
        py3_inst,
        args: [files('icfg.py'), files('icfg.json'), freertos_icfg],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    test('instances',
        py3_inst,
        args: [files('instances.py'), files('instances.json'), freertos_instances],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'sia']
    )

    test('interactions',
        py3_inst,
        args: [files('interactions.py'), files('interactions.json'), freertos_interaction],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'sia']
    )

    test('instance_graph_stats',
        py3_inst,
        args: [files('instance_graph_stats.py'), files('instance_graph_stats.json'), freertos_interaction, 'FreeRTOS'],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'sia']
    )

    test('ir-reader',
        py3_inst,
        args: [files('ir_reader.py'), files('empty.json'), gpslogger_application],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )
    test('ir-reader-false-syntax',
        py3_inst,
        args: [files('ir_reader.py'), files('empty.json'), files('ir_reader.false_syntax.ll')],
        should_fail: true,
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )
    test('ir-reader-multiple-symbols',
        py3_inst,
        args: [files('ir_reader.py'), files('empty.json'), files('ir_reader.multiple_symbols.ll')],
        should_fail: true,
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    test('ir-writer',
        py3_inst,
        args: [files('ir_writer.py'), files('empty.json'), gpslogger_application],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    lock_files = {
                   'autosar_multicore_locks_a': files('locks_a.json'),
                   'autosar_multicore_locks_b': files('locks_b.json'),
                   'autosar_multicore_locks_c': files('locks_c.json'),
                   'autosar_multicore_locks_d': files('locks_d.json'),
                   'autosar_multicore_locks_e': files('locks_e.json'),
                 }
    foreach app: autosar_targets
      if app['full_name'] in lock_files
           locks = lock_files[app['full_name']]
      elif app.has_key('locks')
             locks = app['locks']
      else
        continue
      endif
      if app.has_key('testsuit_extra')
        testsuit_extra = app['testsuit_extra']
      else
        testsuit_extra = []
      endif
      test('lock_elision_' + app['full_name'],
          py3_inst,
          args: [files('lock_elision.py'), locks, app['ll'], app['oil']],
          env: [python_path],
          depends: ara_py,
          suite: ['analysis', 'multisse', 'lock_elision'] + testsuit_extra
      )
      if app.has_key('sys_timings')
        test('lock_elision_with_timings_' + app['full_name'],
             py3_inst,
             args: [files('timed_lock_elision.py'), locks, app['ll'], app['oil'], app['sys_timings']],
             env: [python_path],
             depends: ara_py,
             suite: ['analysis', 'multisse', 'lock_elision', 'timings']
            )
      endif

    endforeach

    foreach app: autosar_targets
      if app['core'] != 'multicore' or not app.has_key('mtrace')
        continue
      endif
      if app.has_key('testsuit_extra')
        testsuit_extra = app['testsuit_extra']
      else
        testsuit_extra = []
      endif
      test('multisse_' + app['full_name'],
          py3_inst,
          args: [files('multisse.py'), app['sys_test'], app['ll'], app['oil']],
          env: [python_path],
          depends: ara_py,
          suite: ['analysis', 'multisse'] + testsuit_extra
      )
    endforeach

    foreach app: autosar_targets
      if not app.has_key('ttrace')
        continue
      endif
      if app.has_key('testsuit_extra')
        testsuit_extra = app['testsuit_extra']
      else
        testsuit_extra = []
      endif
      test('multisse_with_timings_' + app['full_name'],
          py3_inst,
          args: [files('multisse.py'), app['time_test'], app['ll'], app['oil'], app['sys_timings']],
          env: [python_path],
          depends: ara_py,
          suite: ['analysis', 'multisse', 'timings'] + testsuit_extra
      )
    endforeach


    test('multiple-configured-steps',
        py3_inst,
        args: files('multiple_configured_steps.py'),
        env: [python_path],
        suite: ['analysis', 'preproc']
    )


    test('src-loc',
        py3_inst,
        args: [files('src_loc.py'), files('src_loc.json'), freertos_src_loc],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    foreach app : autosar_targets
      if app['core'] != 'singlecore'
        continue
      endif
      test('sse_' + app['full_name'],
          py3_inst,
          args: [files('sse.py'), app['sys_test'], app['ll'], app['oil']],
          env: [python_path],
          depends: ara_py,
          suite: ['analysis', 'sse']
      )
    endforeach

    test('syscall',
        py3_inst,
        args: [files('syscall.py'), files('syscall.json'), freertos_syscall],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    test('value-analysis',
        py3_inst,
        args: [files('value_analysis.py'), files('value_analysis.json'), freertos_svf],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    test('value-analysis-struct',
        py3_inst,
        args: [files('value_analysis.py'), files('value_analysis_struct.json'), freertos_value_analysis_struct],
        env: [python_path],
        depends: ara_py,
        suite: ['analysis', 'preproc']
    )

    subdir('native_step_test')
endif

if get_option('enable_appl_graph_tests')
    subdir('appl_graph_test')
endif

if get_option('enable_zephyr_tests')
    subdir('zephyr_test')
endif

if get_option('enable_posix_tests')
    subdir('posix_test')
endif
