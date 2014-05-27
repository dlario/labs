"""
Server receives:


"""

from __future__ import absolute_import

import zmq
import time
import threading

# local library
import protocol

context = zmq.Context()


def spawn(func):
    thread = threading.Thread(target=func)
    thread.daemon = True
    thread.start()


# Keep track of messages sent
letters = {}


if __name__ == '__main__':
    pull = context.socket(zmq.PULL)  # Incoming messages
    pull.bind("tcp://*:5555")

    pub = context.socket(zmq.PUB)  # Distributing messages
    pub.bind("tcp://*:5556")

    def publisher():
        """
             ________    ___________
            |        |  |           |   /
        --->|  Pull  |--|  Publish  |---|-o
            |________|  |___________|   \

        """

        while True:
            message = pull.recv_json()
            assert message.get('type') == 'envelope'
            envelope = protocol.Envelope.from_message(message)

            if type(envelope.body) is protocol.Letter:
                letter = envelope.body

                if not envelope.author in letters:
                    letters[envelope.author] = {}

                gmtime = time.gmtime(envelope.timestamp)
                asctime = time.asctime(gmtime)
                print "On %s, %s said: %s" % (asctime,
                                              envelope.author,
                                              letter.data)
                letters[envelope.author][envelope.timestamp] = envelope.dump()

                pub.send_json(envelope.dump())

            elif type(envelope.body) is protocol.StateRequest:
                request = envelope.body

                try:
                    author = request.data[0]
                except IndexError:
                    author = envelope.author

                state = letters.get(author)

                print "Getting state for %s" % author
                if state:
                    reply = protocol.StateReply(data=state)
                    envelope = protocol.Envelope(author=envelope.author,
                                                 body=reply,
                                                 recipients=[envelope.author])
                    print "Returning state: %s" % state
                    pub.send_json(envelope.dump())
    spawn(publisher)

    print "Listening for messages @ %s" % "tcp://*:5555"
    print "Broadcasting messages @ %s" % "tcp://*:5556"

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print "\nGood bye"
            break
