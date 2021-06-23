#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

void* new_thread_routine(void* arg) {
    printf("new_thread_routine: arg = \"%s\"\n", (char*)arg);
    pause();
    return NULL;
}

struct ThreadStruct {
    void* (*new_thread_routine)(void* arg);
};

struct ThreadStruct thread_struct;

int main() {
    thread_struct.new_thread_routine = new_thread_routine;
    pthread_t new_thread;
    pthread_create(&new_thread, NULL, thread_struct.new_thread_routine, "test argument");
}