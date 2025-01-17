#!/usr/bin/env python3

import re
def check_vanilla(app_name, modified_app, generated_os, elf):
    assert 'initialized' not in generated_os
def check_passthrough(*args):
    check_vanilla(*args)

def check_instances_full_initialized(app_name, modified_app, generated_os, elf):
    assert 'initialized' in generated_os
    assert not re.search('InitializedStack_t<10+> tzzz_\d+_static_stack', generated_os), 'task zzz darf nicht statisch erzeugt werden'
    assert not re.search('InitializedStack_t<10+> txxx_\d+_static_stack', generated_os), 'task xxx darf nicht statisch erzeugt werden, weil zzz nicht sicher ist'

    assert not re.search('.pxNext = \(ListItem_t \*\) &__queue_head_mutex\d+.xTasksWaitingToSend.xListEnd,', generated_os)
    assert '.pxContainer = &pxReadyTasksLists\[2\]' not in generated_os, "task xxx darf erst zur Laufzeit auf die ready-liste gesetzt werden"

def check_instances_full_static(app_name, modified_app, generated_os, elf):
    assert not re.search('tzzz_\d+_static_stack',generated_os), 'task zzz darf nicht statisch erzeugt werden'
    assert not re.search('txxx_\d+_static_stack',generated_os), 'task xxx darf nicht statisch erzeugt werden, weil zzz nicht sicher ist'
    assert not re.search('extern "C" StaticTask_t tzzz_\d+_tcb;', generated_os)
    assert not re.search('.pxNext = \(ListItem_t \*\) &__queue_head_mutex\d+.xTasksWaitingToSend.xListEnd,', generated_os)
    assert not '__queue_head_mutex' in generated_os, 'mutex darf nicht statisch erzeugt werden, weil zzz nicht statisch ist'
