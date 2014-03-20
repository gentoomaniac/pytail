#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" PyTail
    WIP
    Version 0.1
"""

import logging
import pyinotify
import re
import time


class EventHandlerDirectory(pyinotify.ProcessEvent):
    def __init__(self, stats, opener, closer, reader, restart_file_inotify, filename):
        """docstring for __init__"""
        super(EventHandlerDirectory, self).__init__(stats)
        self._opener = opener
        self._closer = closer
        self._reader = reader
        self._restart_file_inotify = restart_file_inotify
        self._file = filename

    def process_IN_CREATE(self, event):
        """docstring for process_IN_CREATE"""
        if event.pathname == self._file:
            self._restart_file_inotify()
            self._opener()
            self._reader()

    def process_IN_DELETE(self, event):
        if event.pathname == self._file:
            self._closer()

class EventHandlerFile(pyinotify.ProcessEvent):

    def __init__(self, stats, reader):
        """ init
            closer: callback for closing file
            reader: callback for reading file
        """
        super(EventHandlerFile, self).__init__(stats)
        self._reader = reader

    def process_IN_MODIFY(self, event):
        self._reader()

class FileTail():

    def __init__(self, path):
        """docstring for __init__"""
        self._path = path

        # prepare file: on initial open we want to seek to the end
        self._filehandle = None
        self.open()
        self._filehandle.seek(0,2)

        self._setup_file_inotify()
        self._setup_dir_inotify()

    def _setup_file_inotify(self):
        """ setup inotify for the actual file
        """
        watch_manager = pyinotify.WatchManager()  # Watch Manager
        stats = pyinotify.Stats()
        self._notifier_file = pyinotify.ThreadedNotifier(watch_manager, default_proc_fun=EventHandlerFile(stats, self.readline))
        self._notifier_file.start()
        self._wdd_file = watch_manager.add_watch(self._path, pyinotify.IN_MODIFY)

        # setup Inotify for the directory
    def _setup_dir_inotify(self):
        """ setup inotify for the actual file
        """
        path = re.sub(r"/[^/]+$", "", self._path)
        watch_manager = pyinotify.WatchManager()  # Watch Manager
        stats = pyinotify.Stats()
        self._notifier_dir = pyinotify.ThreadedNotifier(watch_manager, default_proc_fun=EventHandlerDirectory(stats, self.open, self.close, self.readline, self._setup_file_inotify, self._path))
        self._notifier_dir.start()
        self._wdd_file = watch_manager.add_watch(path, pyinotify.IN_CREATE | pyinotify.IN_DELETE)


    def open(self):
        """ open file and seek to the end
        """
        try:
            if not self._filehandle:
                self._filehandle = open(self._path)
        except IOError, e:
            raise e

    def close(self):
        """ close the file
        """
        if self._filehandle:
            self._filehandle.close()
            self._filehandle = None

    def readline(self):
        """ read line from the file
        """
        if self._filehandle:
            line = self._filehandle.readline()
            self._send_to_syslog(line)

    def _send_to_syslog(self, line):
        """ handle the sending to syslog
        """
        print line

    def run(self):
        """ start main processing
        """
        while True:
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                self._notifier_file.stop()
                self._notifier_dir.stop()
                break
            except:
                self._notifier_file.stop()
                self._notifier_dir.stop()
                raise

def main():
    """ main program
    """
    logging.info('I am an informational log entry in the sample script.')
    app = FileTail('/home/freak/test.in')
    app.run()

if __name__ == '__main__':
    main()
