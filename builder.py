#!/usr/bin/python -OO
'''
builder is a program to create and manage machines in chroot environment.
'''
import os
import sys
from optparse import OptionParser
from configobj import ConfigObj

__app__ = os.path.basename(sys.argv[0])
__maintainer__ = 'Robert Smol <robert.smol@stereoit.com>'

__license__ = ''' Distributed under the terms of the GNU General Public License version 2
 builder comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to
  redistribute it under certain conditions. See /usr/lib/metro/LICENSE for details.
'''
__status__='Development'
__version__='0.1'
  
#some defaults
_defaultConfigFile = '/etc/builder/builder.conf' 


def version():
    print ' '+__app__,'version',__version__
    print
    print ' Copyright 2009 StereoIT ; Portions copyright 2003-2007 Gentoo Foundation and Funtoo Technologies LLC'
    print ' Maintainer:',__maintainer__
    print
    print ' Web: http://www.stereoit.com'
    print ' Project: http://github.com/stereoit/builder/wikis'
    print
    print __license__


def initSettings(configFile='/etc/builder/builder.conf'):
    config = ConfigObj()
    if os.path.exists(configFile):
        emitMessage('Parsing %s' % configFile)
        #print('Parsing %s' % configFile)
        config.filename = configFile
        config.reload()
    else:
        print 'Warning: %s not found' % configFile
        
    return config


def emitMessage(msg, quiet=False):
    '''
    Prints out messages and includes verbose and quite flags.
    '''
    if settings['quiet']:
        return
    print msg


def initMachine(machine):
    '''
    Responsible for creatin directory structure for chroot of the virtual
    machine.
    '''
    emitMessage('initMachine() called [%s]' % machine)
    pass

def main():
    #check if user is root
#    if os.getuid() != 0: 
#        print __app__ + ': This script requires root privileges to operate.'
#        sys.exit(2)


    #parse arguments and define action
    usage = 'usage: %prog [options] <machine>'
    parser = OptionParser(usage=usage)
    parser.add_option('-i', '--init', dest='initMachine',
            help='initalizes machine environment',
            action='store_true', default=False)
    parser.add_option('-c', '--config', dest='configFile', 
            help='builder configuration file [/etc/builder/builder.conf]', 
            metavar='configFile', default='/etc/builder/builder.conf')
    parser.add_option('-q', '--quiet', action='store_false', dest='verbose', default=True,
                  help="don't print status messages to stdout")

    (options, args) = parser.parse_args()
    
    if len(sys.argv) < 2 :
        parser.error('incorrect number of arguments') 
        sys.exit(2)

    global settings
    settings = {}

    #handle --verbose and --quiet options
    settings['quiet'] = not options.verbose 

    #initalize builder settings
    if options.configFile:
        configFile = options.configFile
    else:
        configFile = _defaultConfigFile
    settings = initSettings(configFile)
    settings['quiet'] = not options.verbose 


    #handle actions
    if options.initMachine:
        initMachine(args[0])

#main loop, if called as a program start main
if __name__ == '__main__':
    main()

