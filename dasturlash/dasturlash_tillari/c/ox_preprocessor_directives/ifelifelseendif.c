#include <stdio.h>
#include <stdlib.h>

#define arch 64

int main()
{
  #if arch == 32
    printf("32 bit architecture\n");
  #elif arch == 64
    printf("64 bit architecture\n");
  #else
    printf("Unknown architecture\n");
  #endif

  return 0;
}

