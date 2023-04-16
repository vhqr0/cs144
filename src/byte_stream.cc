#include <algorithm>
#include <stdexcept>

#include "byte_stream.hh"

using namespace std;

ByteStream::ByteStream( uint64_t capacity )
  : capacity_( capacity ), buffer_(), closed_( false ), error_( false ), bytes_pushed_( 0 ), bytes_popped_( 0 )
{}

void Writer::push( string data )
{
  uint64_t to_push = min( data.length(), available_capacity() );
  buffer_ += data.substr( 0, to_push );
  bytes_pushed_ += to_push;
}

void Writer::close()
{
  closed_ = true;
}

void Writer::set_error()
{
  error_ = true;
}

bool Writer::is_closed() const
{
  return closed_;
}

uint64_t Writer::available_capacity() const
{
  return capacity_ - buffer_.length();
}

uint64_t Writer::bytes_pushed() const
{
  return bytes_pushed_;
}

string_view Reader::peek() const
{
  return buffer_;
}

bool Reader::is_finished() const
{
  return buffer_.empty() && closed_;
}

bool Reader::has_error() const
{
  return error_;
}

void Reader::pop( uint64_t len )
{
  uint64_t to_pop = min( buffer_.length(), len );
  buffer_ = buffer_.substr( to_pop );
  bytes_popped_ += to_pop;
}

uint64_t Reader::bytes_buffered() const
{
  return buffer_.length();
}

uint64_t Reader::bytes_popped() const
{
  return bytes_popped_;
}
