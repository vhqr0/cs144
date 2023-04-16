#include "reassembler.hh"

using namespace std;

Reassembler::Piece::Piece( uint64_t first, uint64_t last, std::string data, bool eof )
  : first_( first ), last_( last ), data_( data ), eof_( eof )
{}

Reassembler::Reassembler() : pieces_() {}

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

  list<Piece> new_pieces;
  bool piece_pushed = false;
  for ( const Piece& p : pieces_ ) {
    if ( piece_pushed || p.last_ < first_index ) {
      new_pieces.push_back( p );
      continue;
    }
    if ( p.first_ > last_index ) {
      new_pieces.push_back( Piece( first_index, last_index, data, is_last_substring ) );
      piece_pushed = true;
      new_pieces.push_back( p );
      continue;
    }
    if ( p.first_ < first_index ) {
      data = p.data_.substr( 0, first_index - p.first_ ) + data;
      first_index = p.first_;
    }
    if ( is_last_substring )
      break;
    if ( p.last_ >= last_index ) {
      data += p.data_.substr( last_index - p.first_ );
      last_index = p.last_;
      is_last_substring = p.eof_;
    }
  }
  if ( !piece_pushed )
    new_pieces.push_back( Piece( first_index, last_index, data, is_last_substring ) );
  swap( new_pieces, pieces_ );

  const Piece& front = pieces_.front();
  if ( front.first_ == min_index ) {
    output.push( front.data_ );
    if ( front.eof_ )
      output.close();
    pieces_.pop_front();
  }
}

uint64_t Reassembler::bytes_pending() const
{
  uint64_t bytes = 0;
  for ( const Piece& p : pieces_ ) {
    bytes += p.data_.length();
  }
  return bytes;
}
