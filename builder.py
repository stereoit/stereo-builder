#!/usr/bin/python -OO
'''
builder is a program to create and manage machines in chroot environment.
'''
import os
import sys
import commands
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
_defaultConfigFile = 'etc/builder/builder.conf' 


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


def init_settings(configFile='/etc/builder/builder.conf'):
    config = ConfigObj()
    if os.path.exists(configFile):
        emit_message('Parsing %s' % configFile)
        #print('Parsing %s' % configFile)
        config.filename = configFile
        config.reload()
    else:
        print 'Warning: %s not found (no configuration loaded)' % configFile
        
    return config


def emit_message(msg, quiet=False):
    '''
    Prints out messages and includes verbose and quite flags.
    '''
#    if settings['verbose']:
    print msg


def init_machine(machine):
    '''
    Responsible for creating directory structure for chroot of the virtual
    machine including unpacking stage4 and linking given portage and packages
    directories.
    '''
    emit_message('init_machine() called [%s]' % machine)
    _results = {}
    status = 0
    #test if machine dir exists in chroots
    machine_chroot = settings['config']['general']['chroots_top']+'/'+settings['machine']['name']
    if os.path.exists(machine_chroot):
        print 'Machine directory [%s] already exists ..exiting' % machine_chroot
        sys.exit(2)
    else:
        #create it
        emit_message('\tcreating [%s]' % machine_chroot)
        _ensure_dir(machine_chroot)
    
    #now unpack the backup there
    stage4_backup = settings['config']['general']['stage4_top'] + '/' + settings['machine']['stage4']
    emit_message('\tunpacking stage4 [%s]' % stage4_backup)
    if not os.path.exists(stage4_backup):
        print 'No valid stage4 (backup) machine image provided [%s] ..exiting' % stage4_backup
        sys.exit(2)
    else:  
        #unpack the file
        os.chdir(machine_chroot)
        (status, _results['unpack_log']) = commands.getstatusoutput('tar xjvpf %s' % stage4_backup)
        
    #link portage tree ---- NOT NEEDED this will be part of screen command
#    portage_tree = settings['config']['general']['portage_trees']+ '/' + settings['machine']['portage']
#    if not os.path.exists(portage_tree):
#        print 'Error: selected portage tree [%s] does not exists in ..exiting' % portage_tree
#        sys.exit(2)
#    _ensure_dir(machine_chroot + '/usr/portage')
#    os.chdir(machine_chroot + '/usr/')
    #TODO this should be either a symbolic link or when we screen to the machine as this solution
    # will not persists over reboot
#    (status, _results['portage_log']) = commands.getstatusoutput('mount -o bind %s %s' % (portage_tree,'portage'))

    #link packages dir
    _emit_message('\tlinking pkgbin directory')
    machine_pkg_dir = machine_chroot + '/srv/packages'  
    pkg_dir = settings['config']['general']['pkgbin_top']
    _ensure_dir(pkg_dir)
    _ensure_dir(machine_pkg_dir)
    os.chdir(pkg_dir)
    os.symlink(machine_pkg_dir, settings['machine']['name'])

    os.chdir(settings['cwd'])
    return _results

def _ensure_dir(dir):
    '''
    Responsible for creating directories if they do not exists
    '''
    if not os.path.exists(dir):
        os.makedirs(dir)
    

def screen_to_machine(machine):
    '''
    Checks whether the bin/sh exists in chroot directory and creates
    screen connection with chroot.
    '''
    emit_message('screen_to_machine() called [%s]' % machine)
    pass

def main():
    #check if user is root
#    if os.getuid() != 0: 
#        print __app__ + ': This script requires root privileges to operate.'
#        sys.exit(2)


    #parse arguments and define action
    usage = 'usage: %prog [options] <machine>'
    parser = OptionParser(usage=usage)
    parser.add_option('-s', '--screen', dest='screen',
            help='ensures some checks and swith to machine via screen',
            action='store_true', default=False)
    parser.add_option('-i', '--init', dest='init_machine',
            help='initalizes machine environment',
            action='store_true', default=False)
    parser.add_option('-m', '--machine', dest='machineConfig', 
            help='machine configuration file [/etc/builder/machine.conf]',
            metavar='machineConfig')
    parser.add_option('-c', '--config', dest='configFile', 
            help='builder configuration file [/etc/builder/builder.conf]', 
            metavar='configFile', default='/etc/builder/builder.conf')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False,
                  help="Print some verbose messages")

    (options, args) = parser.parse_args()
    
    if len(args) < 1 :
        parser.error('incorrect number of arguments') 
        sys.exit(2)

    global settings
    settings = {}

    #handle --verbose and --quiet options
    settings['verbose'] = options.verbose 

    #initalize builder settings
    if options.configFile:
        configFile = options.configFile
    else:
        configFile = _defaultConfigFile
    settings['config'] = init_settings(configFile).dict()
    settings['cwd'] = os.getcwd()

    #machine config test
    machine = args[0]
    if options.machineConfig:
        machineConfigPath = options.machineConfig
    else:
        machineConfigPath = os.path.dirname(configFile) + '/' + machine + '.conf'
    if not os.path.exists(machineConfigPath) :
        print 'Cannot find machine config %s ..exiting' % machineConfigPath
        sys.exit(2)
    else:
        settings['machine'] = init_settings(configFile=machineConfigPath).dict()

    #dump settings if verbose
    if options.verbose:
        print settings

    #handle actions
    if options.init_machine:
        init_machine(machine)

#main loop, if called as a program start main
if __name__ == '__main__':
    main()

