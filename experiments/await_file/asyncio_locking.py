#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import os
import os.path
import time
import asyncio

import aioprocessing
import pylru
import filetype


def read_message(folder_name, msg_idx):
    try:
        start = time.time()
        file_name = os.path.join(folder_name, msg_idx)
        with open(file_name, 'rb') as f:
            msg = f.read()
        time.sleep(1)
        total_time = time.time() - start
        ftype = filetype.guess(file_name)
        print(f"Read in file {file_name}, type: {ftype}, took: {total_time}")
        return ({'file_type': ftype,
                 'length': len(msg),
                 'time_to_read': total_time})
    except Exception as e:
        print(f"file {file_name}, exception: {e}")
        return None


########################################################################
########################################################################
#
class MessageStore(object):

    ####################################################################
    #
    def __init__(self):
        self.msg_cache_lock = asyncio.Lock()
        self.msg_cache = pylru.lrucache(100)
        self.msg_cache_futures = {}
        self.pool = aioprocessing.AioPool(processes=4)

    async def fetch_msg(self, folder, msg_idx):
        cache_key = f'{folder}/{msg_idx}'

        # This boolean is used to indicate that we need to send a
        # request to the pool of worker processes to read a
        # message. This is done as a boolean flag so the act of
        # requesting that we read a message is done outside of the
        # self.msg_cache_lock.
        #
        read_msg = False
        async with self.msg_cache_lock:
            if cache_key in self.msg_cache:
                return self.msg_cache[cache_key]
            if cache_key in self.msg_cache_futures:
                read_msg_future = self.msg_cache_futures[cache_key]
            else:
                read_msg_future = asyncio.get_running_loop().create_future()
                self.msg_cache_futures[cache_key] = read_msg_future
                read_msg = True

        # If we need to read the message from disk put a message on to the
        # queue for the message reading pool processors to read the
        # message and set the future when the result arrives. Done via a
        # boolean flag to have the message being put on the queue outside
        # of the self.msg_cache_lock.
        #
        if read_msg:
            msg = await self.pool.coro_apply(read_message,
                                             (folder, msg_idx))
            async with self.msg_cache_lock:
                self.msg_cache[cache_key] = msg
                # NOTE: outside of this lock we can not guarantee that
                # the future we created above is the one that we want
                # to delete now so instead of relying on the future
                # cache being the same we only deal with the future
                # cache while we are inside this lock.
                #
                if cache_key in self.msg_cache_futures:
                    read_msg_future = self.msg_cache_futures[cache_key]
                    del self.msg_cache_futures[cache_key]
                    try:
                        read_msg_future.set_result(msg)
                    except InvalidStateError:
                        # If the future is already done then that is
                        # okay.. ignore it and move on.
                        #
                        pass
            return msg

        # We are another attempt to read the same message from the
        # subprocess. Use the existing future to wait for the result.
        #
        return await read_msg_future


async def main(loop):
    msg_store = MessageStore()

    d = "/Users/scanner/tmp/manga/soredemo_boku_wa_kimi_ga_suki"
    fnames = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
    tasks = []
    for fname in fnames:
        tasks.append(msg_store.fetch_msg(d, fname))
    await asyncio.gather(*tasks)
    for t in tasks:
        print(t)


event_loop = asyncio.get_event_loop()
try:
    event_loop.run_until_complete(main(event_loop))
finally:
    event_loop.close()
