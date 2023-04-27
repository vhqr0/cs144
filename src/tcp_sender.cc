#include "tcp_config.hh"
#include "tcp_sender.hh"

#include <random>

using namespace std;

TCPSender::Segment::Segment( uint64_t first, string data, bool bof, bool eof )
  : first_( first ), last_( first + data.length() + bof + eof ), data_( data ), bof_( bof ), eof_( eof )
{}

TCPSender::Segment::Segment( uint64_t first, uint64_t last, string data, bool bof, bool eof )
  : first_( first ), last_( last ), data_( data ), bof_( bof ), eof_( eof )
{}

TCPSenderMessage TCPSender::Segment::message( Wrap32 isn )
{
  return { Wrap32::wrap( first_, isn ), bof_, data_, eof_ };
}

/* TCPSender constructor (uses a random ISN if none given) */
TCPSender::TCPSender( uint64_t initial_RTO_ms, optional<Wrap32> fixed_isn )
  : isn_( fixed_isn.value_or( Wrap32 { random_device()() } ) )
  , initial_RTO_ms_( initial_RTO_ms )
  , RTO_ms_( initial_RTO_ms_ )
  , TO_ms_( 0 )
  , consecutive_retransmissions_( 0 )
  , seqno_( 0 )
  , ackno_( 0 )
  , winsize_( 0 )
  , segs_( { { 0, 1, "", true, false } } )
  , outstanding_segs_()
  , eof_sent_( false )
{}

uint64_t TCPSender::sequence_numbers_in_flight() const
{
  return ( segs_.empty() ? seqno_ : segs_.back().last_ ) - ackno_;
}

uint64_t TCPSender::consecutive_retransmissions() const
{
  return consecutive_retransmissions_;
}

optional<TCPSenderMessage> TCPSender::maybe_send()
{
  if ( segs_.empty() )
    return nullopt;

  Segment seg = segs_.front();
  segs_.pop_front();
  if ( seg.last_ > seqno_ ) { // first trans
    seqno_ = seg.last_;
    if ( outstanding_segs_.empty() )
      TO_ms_ = RTO_ms_;
    outstanding_segs_.push_back( seg );
  }
  return seg.message( isn_ );
}

void TCPSender::push( Reader& outbound_stream )
{
  if ( eof_sent_ )
    return;

  uint64_t max_to_push = ackno_ + max( 1UL, winsize_ ) - ( segs_.empty() ? seqno_ : segs_.back().last_ );
  uint64_t to_push = min( max_to_push, outbound_stream.bytes_buffered() );
  std::string buffer( outbound_stream.peek().substr( 0, to_push ) );
  outbound_stream.pop( to_push );

  while ( !buffer.empty() ) {
    if ( segs_.empty() || segs_.back().data_.length() >= TCPConfig::MAX_PAYLOAD_SIZE ) {
      uint64_t seqno = segs_.empty() ? seqno_ : segs_.back().last_;
      segs_.push_back( { seqno, seqno, "", false, false } );
    }
    uint64_t to_fill = min( TCPConfig::MAX_PAYLOAD_SIZE - segs_.back().data_.length(), buffer.length() );
    segs_.back().data_ += buffer.substr( 0, to_fill );
    segs_.back().last_ += to_fill;
    buffer = buffer.substr( to_fill );
  }
  if ( to_push < max_to_push && outbound_stream.is_finished() ) {
    if ( segs_.empty() ) {
      uint64_t seqno = segs_.empty() ? seqno_ : segs_.back().last_;
      segs_.push_back( { seqno, seqno + 1, "", false, true } );
    } else {
      segs_.back().eof_ = true;
      ++segs_.back().last_;
    }
    eof_sent_ = true;
  }
}

TCPSenderMessage TCPSender::send_empty_message() const
{
  return { Wrap32::wrap( seqno_, isn_ ), false, {}, false };
}

void TCPSender::receive( const TCPReceiverMessage& msg )
{
  if ( msg.ackno == nullopt ) {
    winsize_ = msg.window_size;
    return;
  }

  uint64_t ackno = msg.ackno.value().unwrap( isn_, seqno_ );
  if ( ackno > seqno_ )
    return;
  bool refresh = false;
  while ( !outstanding_segs_.empty() ) {
    Segment& seg = outstanding_segs_.front();
    if ( ackno < seg.last_ )
      break;
    refresh = true;
    outstanding_segs_.pop_front();
  }

  uint64_t edge = max( ackno + msg.window_size, ackno_ + winsize_ );
  ackno_ = max( ackno, ackno_ );
  winsize_ = edge - ackno_;

  if ( !refresh )
    return;

  RTO_ms_ = initial_RTO_ms_;
  if ( !outstanding_segs_.empty() )
    TO_ms_ = RTO_ms_;
  consecutive_retransmissions_ = 0;
}

void TCPSender::tick( const size_t ms_since_last_tick )
{
  if ( outstanding_segs_.empty() )
    return;
  if ( ms_since_last_tick < TO_ms_ ) {
    TO_ms_ -= ms_since_last_tick;
    return;
  }
  segs_.push_front( outstanding_segs_.front() );
  if ( winsize_ != 0 || outstanding_segs_.front().bof_ ) {
    ++consecutive_retransmissions_;
    RTO_ms_ *= 2;
  }
  TO_ms_ = RTO_ms_;
}
