#include "reassembler.hh"

using namespace std;

Reassembler::Segment::Segment( uint64_t first, std::string data, bool eof )
  : first_( first ), last_( first + data.length() ), data_( data ), eof_( eof )
{}

Reassembler::Segment::Segment( uint64_t first, uint64_t last, std::string data, bool eof )
  : first_( first ), last_( last ), data_( data ), eof_( eof )
{}

Reassembler::Reassembler() : segs_() {}

void Reassembler::insert( uint64_t first_index, string data, bool is_last_substring, Writer& output )
{
  uint64_t min_index = output.bytes_pushed();
  uint64_t max_index = min_index + output.available_capacity();
  uint64_t last_index = first_index + data.length();

  if ( first_index > max_index || last_index < min_index )
    return;

  if ( last_index > max_index ) {
    data = data.substr( 0, max_index - first_index );
    last_index = max_index;
  }
  if ( first_index < min_index ) {
    data = data.substr( min_index - first_index );
    first_index = min_index;
  }

  list<Segment> new_segs;
  bool segment_pushed = false;
  for ( const Segment& s : segs_ ) {
    if ( segment_pushed || s.last_ < first_index ) {
      new_segs.push_back( s );
      continue;
    }
    if ( s.first_ > last_index ) {
      new_segs.push_back( Segment( first_index, last_index, data, is_last_substring ) );
      segment_pushed = true;
      new_segs.push_back( s );
      continue;
    }
    if ( s.first_ < first_index ) {
      data = s.data_.substr( 0, first_index - s.first_ ) + data;
      first_index = s.first_;
    }
    if ( is_last_substring )
      break;
    if ( s.last_ >= last_index ) {
      data += s.data_.substr( last_index - s.first_ );
      last_index = s.last_;
      is_last_substring = s.eof_;
    }
  }
  if ( !segment_pushed )
    new_segs.push_back( Segment( first_index, last_index, data, is_last_substring ) );
  swap( new_segs, segs_ );

  const Segment& front = segs_.front();
  if ( front.first_ == min_index ) {
    output.push( front.data_ );
    if ( front.eof_ )
      output.close();
    segs_.pop_front();
  }
}

uint64_t Reassembler::bytes_pending() const
{
  uint64_t bytes = 0;
  for ( const Segment& s : segs_ ) {
    bytes += s.data_.length();
  }
  return bytes;
}
