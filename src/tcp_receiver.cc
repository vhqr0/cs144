#include "tcp_receiver.hh"

using namespace std;

TCPReceiver::TCPReceiver() : isn_( 0 ), initialized_( false ) {}

void TCPReceiver::receive( TCPSenderMessage message, Reassembler& reassembler, Writer& inbound_stream )
{
  if ( message.SYN ) {
    initialized_ = true;
    isn_ = message.seqno;
    message.seqno = message.seqno + 1;
  }
  uint64_t index = message.seqno.unwrap( isn_, inbound_stream.bytes_pushed() ) - 1;
  reassembler.insert( index, message.payload, message.FIN, inbound_stream );
}

TCPReceiverMessage TCPReceiver::send( const Writer& inbound_stream ) const
{
  uint64_t ws = inbound_stream.available_capacity();
  if ( ws > 0xffff )
    ws = 0xffff;
  if ( !initialized_ )
    return TCPReceiverMessage { nullopt, (uint16_t)ws };
  Wrap32 ackno = Wrap32::wrap( inbound_stream.bytes_pushed() + 1, isn_ );
  if ( inbound_stream.is_closed() )
    ackno = ackno + 1;
  return TCPReceiverMessage { ackno, (uint16_t)ws };
}
