#include "platform.h"

const char *platform_name(void)
{
#if defined(MYAPP_WINDOWS)

    return "Windows";

#elif defined(MYAPP_MACOS)

    return "macOS";

#elif defined(MYAPP_LINUX)

    return "Linux";

#else

    return "Unknown";

#endif
}