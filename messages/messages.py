#!/usr/bin/env python

import sys, os, json

def main():
    myfolder = sys.path[0]
    files = os.listdir(myfolder)
    messages = dict()
    for file in files:
        if not file.endswith('.txt'): continue
        basename = file[:-4]
        messages[basename] = os.path.join('messages', file)
    messages_file = os.path.join(myfolder, '..', 'messages.json')
    with open(messages_file, 'w') as fp:
        json.dump(messages, fp)

if __name__ == '__main__':
    main()
