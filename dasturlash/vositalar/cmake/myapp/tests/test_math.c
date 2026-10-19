#include <assert.h>

#include "myapp/math_utils.h"

int main(void)
{
    assert(add(2, 3) == 5);
    assert(subtract(10, 4) == 6);

    return 0;
}