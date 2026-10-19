#include <stdio.h>

#include "myapp/math_utils.h"
#include "platform.h"

int main(void)
{
    printf("MyApp 1.0\n");
    printf("Platform: %s\n", platform_name());

    printf("10 + 5 = %d\n", add(10, 5));
    printf("10 - 5 = %d\n", subtract(10, 5));

    return 0;
}