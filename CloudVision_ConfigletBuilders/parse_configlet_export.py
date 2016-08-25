#!/usr/bin/python
#
# Copyright (c) 2016, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import os
import json
import argparse
import tempfile
import shutil
import zipfile
import logging

logger = logging.getLogger(__name__)

class ExtractFileException(Exception):
    pass

def extract_file(fname, tmpDir):
    '''
    '''
    fileName = None
    try:
        zipf = zipfile.ZipFile(fname, 'r')
    except zipfile.BadZipfile:
        raise
    for member in zipf.namelist():
        name = str(member)
        if name.startswith('configletDataFile'):
            fileName = name
            break
    if not fileName:
        raise ExtractFileException('No configlet data file contained')
    zipf.extractall(tmpDir)
    db = {}
    fObject = open(os.path.join(tmpDir, fileName), 'r')
    db = json.load(fObject)
    fObject.close()
    return db


def getConfigletBuilderData(db):
    ''' 
    '''
    data = []
    mainScript = ""
    for configletInfo in db['data']['configletBuilder']:
        if isinstance(configletInfo['main_script'], dict):
            mainScript = configletInfo['main_script']['data']
        else:
            mainScript = configletInfo['main_script']

        data.append(
            dict({
                'name':configletInfo['name'],
                'main':mainScript,
                })
        )
    return data


def parse_out_main(fname, tmpDir, force=True):
    '''
    '''
    data = extract_file(fname, tmpDir)
    configlet_data = getConfigletBuilderData(data)
    for configlet_info in configlet_data:
        if not force and os.path.isfile(configlet_info['name']):
            cont = raw_input("File \'{}\' exists. Overwrite? [y/n]: ".format(configlet_info['name']))
            if not cont.lower() in ("y", "yes"):
                return
        with open(configlet_info['name'], 'w+') as f:
            f.write(configlet_info['main'])
        logging.info('Created file \'%s\'', configlet_info['name'])
    return

def parseArgs():
    '''
    '''
    parser = argparse.ArgumentParser(description='CVP Configlet Export Parser')
    parser.add_argument('filename', help='Exported zip\'d CVP Configlet file')
    parser.add_argument('--force', action='store_true', help='Force overwrite', default=False)
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output', default=False)
    args = parser.parse_args()
    # return namespace object returned from parse_args.
    # If dict() is required, then wrap with vars()
    return args

def main():
    options = parseArgs()
    tmpDir = tempfile.mkdtemp()
    
    if options.verbose:
        logging.basicConfig(
            format=u'%(levelname)s: %(message)s',
            level=logging.INFO)

    try:
        parse_out_main(options.filename, tmpDir, options.force)
    finally:
        shutil.rmtree(tmpDir)

if __name__ == '__main__':
    main()
