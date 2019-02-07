#!/usr/bin/env python3
#
# File: $Id$
#
"""
Testing using multi-processing and many processes per user with
caching and file retrieval and parsing.

This is going to test having three things:

1) an in-memory LRU cache of parsed messages the key is the file path
2) a pool of workers dedicated to returning requested message objects,
   if in the cache returns them from the cache. If not reads them from
   disk, parses them, and puts them in the cache. It will know to
   check if a message is already in the cache then check file's last
   modify time and size to see if they have changed.
3) a pool of workers that will be asked to retrieve random messages
   and print out some statistics.
"""

# system imports
#
import multiprocessing


########################################################################
########################################################################
#
class MessageBoxPlayground(object):

    ####################################################################
    #
    def __init__(self, ):
        self.msg_reader_pool = multiprocessing.Pool(5)
        self.mbox_pool = multiprocessing.Pool(5)

    ####################################################################
    #
    def run(self):
        pass


#############################################################################
#
def main():
    mb_playground = MessageBoxPlayground()
    mb_playground.run()


############################################################################
############################################################################
#
# Here is where it all starts
#
if __name__ == '__main__':
    main()
#
############################################################################
############################################################################
