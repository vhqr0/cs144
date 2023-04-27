#pragma once

#include "byte_stream.hh"
#include "tcp_receiver_message.hh"
#include "tcp_sender_message.hh"

#include <list>

class TCPSender
{
  struct Segment {
    uint64_t first_, last_;
    std::string data_;
    bool bof_, eof_;

    Segment( uint64_t first, std::string data, bool bof, bool eof );
    Segment( uint64_t first, uint64_t last, std::string data, bool bof, bool eof );

    TCPSenderMessage message(Wrap32 isn);
  };

  Wrap32 isn_;
  uint64_t initial_RTO_ms_;

  uint64_t RTO_ms_;
  uint64_t TO_ms_;
  uint64_t consecutive_retransmissions_;
  uint64_t seqno_;
  uint64_t ackno_;
  uint64_t winsize_;
  std::list<Segment> segs_;
  std::list<Segment> outstanding_segs_;
  bool eof_sent_;

public:
  /* Construct TCP sender with given default Retransmission Timeout and possible ISN */
  TCPSender( uint64_t initial_RTO_ms, std::optional<Wrap32> fixed_isn );

  /* Push bytes from the outbound stream */
  void push( Reader& outbound_stream );

  /* Send a TCPSenderMessage if needed (or empty optional otherwise) */
  std::optional<TCPSenderMessage> maybe_send();

  /* Generate an empty TCPSenderMessage */
  TCPSenderMessage send_empty_message() const;

  /* Receive an act on a TCPReceiverMessage from the peer's receiver */
  void receive( const TCPReceiverMessage& msg );

  /* Time has passed by the given # of milliseconds since the last time the tick() method was called. */
  void tick( uint64_t ms_since_last_tick );

  /* Accessors for use in testing */
  uint64_t sequence_numbers_in_flight() const;  // How many sequence numbers are outstanding?
  uint64_t consecutive_retransmissions() const; // How many consecutive *re*transmissions have happened?
};
