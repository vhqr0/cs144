#include "wrapping_integers.hh"

using namespace std;

Wrap32 Wrap32::wrap( uint64_t n, Wrap32 zero_point )
{
  return Wrap32( n + zero_point.raw_value_ );
}

uint64_t Wrap32::unwrap( Wrap32 zero_point, uint64_t checkpoint ) const
{
  uint32_t n = raw_value_ - zero_point.raw_value_;
  uint32_t cl = (uint32_t)checkpoint;
  uint64_t ch = ( checkpoint & 0xffffffff00000000 );
  if ( n == cl )
    return ch + n;
  if ( ( n - cl ) < ( cl - n ) )
    return n > cl ? ch + n : ch + n + 0x100000000;
  else
    return n < cl ? ch + n : ( ch == 0 ? n : ch + n - 0x100000000 ); // prefer more than 0
}
