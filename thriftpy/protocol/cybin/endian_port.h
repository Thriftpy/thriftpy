
#if defined(__APPLE__)
static inline int16_t bswap16(int16_t n) {
    return (n << 8) | (n >> 8);
}

static inline int32_t bswap32(int32_t n) {
    return ((n & 0xff000000) >> 24) | \
           ((n & 0x00ff0000) >>  8) | \
           ((n & 0x0000ff00) <<  8) | \
           ((n & 0x000000ff) << 24);
}

static inline int64_t bswap64(int64_t n) {
    return ((n & 0xff00000000000000ull) >> 56) | \
           ((n & 0x00ff000000000000ull) >> 40) | \
           ((n & 0x0000ff0000000000ull) >> 24) | \
           ((n & 0x000000ff00000000ull) >> 8)  | \
           ((n & 0x00000000ff000000ull) << 8)  | \
           ((n & 0x0000000000ff0000ull) << 24) | \
           ((n & 0x000000000000ff00ull) << 40) | \
           ((n & 0x00000000000000ffull) << 56);
}

#define htobe16(n) bswap16(n)
#define htobe32(n) bswap32(n)
#define htobe64(n) bswap64(n)
#define be16toh(n) bswap16(n)
#define be32toh(n) bswap32(n)
#define be64toh(n) bswap64(n)

#else

#include <endian.h>
#include <byteswap.h>

#ifndef htobe16
#define htobe16(x) bswap_16(x)
#endif

#ifndef htobe32
#define htobe32(x) bswap_32(x)
#endif

#ifndef htobe64
#define htobe64(x) bswap_64(x)
#endif

#ifndef be16toh
#define be16toh(x) bswap_16(x)
#endif

#ifndef be32toh
#define be32toh(x) bswap_32(x)
#endif

#ifndef be64toh
#define be64toh(x) bswap_64(x)
#endif

#endif
