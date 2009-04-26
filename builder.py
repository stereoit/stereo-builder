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
    _check_path_or_die(stage4_backup, 
         msg='No valid stage4 (backup) machine image provided [%s] ..exiting' % stage4_backup)
    #unpack the file
    os.chdir(machine_chroot)
    (status, _results['unpack_log']) = commands.getstatusoutput('tar xjvpf %s' % stage4_backup)
        
    #link packages dir
    emit_message('\tlinking pkgbin directory')
    machine_pkg_dir = machine_chroot + '/srv/packages'  
    pkg_dir = settings['config']['general']['pkgbin_top']
    _ensure_dir(pkg_dir)
    _ensure_dir(machine_pkg_dir)
    os.chdir(pkg_dir)
    os.symlink(machine_pkg_dir, settings['machine']['name'])

    os.chdir(settings['cwd'])
    return _results

def _check_path_or_die(path, msg=None):
    '''
    Check whether given path exists or print message and die.
    '''
    msg = msg and msg or 'Missing path [%s] ..exiting' % path 
    if not os.path.exists(path):
        print msg
        sys.exit(2)

def _ensure_dir(dir):
    '''
    Responsible for creating directories if they do not exists
    '''
    if not os.path.exists(dir):
        os.makedirs(dir)
    

def screen_attach(machine):
    '''
    Responsible for checking that all mountpoints are mounted (sys,proc,
    portage and stuff).
    Then it should:
    basic checks (directories exists and such)
    create screen
    chroot to machine
    disconnect from screen
    write message to user how to access the machine
    '''
    emit_message('screen_to_machine() called [%s]' % machine)
    #check if machine directory exists
    machine_chroot =  settings['config']['general']['chroots_top']+'/'+settings['machine']['name']
    _check_path_or_die(machine_chroot)

    #check for proc mounted and mount
    proc_mount = machine_chroot + '/proc'
    _check_path_or_die(proc_mount)
    _check_and_mount('proc',proc_mount,'proc')
    #check for sys mounted and mount
    sys_mount = machine_chroot + '/sys'
    _check_path_or_die(sys_mount)
    _check_and_mount('sys',sys_mount,'sysfs')
    #check for portage mounted and mount
    portage_mount = machine_chroot + '/usr/portage'
    portage = settings['config']['general']['portage_trees'] + '/' + settings['machine']['portage']
    _check_path_or_die(portage_mount)
    _check_path_or_die(portage)
    _check_and_mount(portage,portage_mount)

    #check if screen does not exists already for given machine otherwise start it
    (status, result) = commands.getstatusoutput('screen -list|grep builder.%s' % machine)
    message = '''
    Everything mounted, please issue following commands to login to machine environment:
    screen -R builder.%s
    ''' % machine
    if not status:
        emit_message('\tScreen already exists .. skipping')
        message = '''
        Everything mounted, but screen session builder.%s already exists. To log into machine issue:
        screen -R builder.%s.2
        chroot %s
        and set new PS1 with
        export PS1='\[\033[01;31m\]\h\[\033[01;34m\] \W \$\[\033[00m\] '
        ''' % (machine,machine,machine_chroot)
    else:        
        #create bashrc and run initial screen and chroot into it
        _create_bash_rcfile(machine_chroot + '/tmp/builder_bashrc', machine)
        commands.getstatusoutput('screen -dmS builder.%s chroot %s /bin/bash --rcfile /tmp/builder_bashrc' % (machine, machine_chroot))
    emit_message(message)

def screen_dettach(machine):
    '''
    After screen session is over, unmount variuos directories for cleanup.
    '''
    emit_message('Deactivating screen from [%s]' % machine)
    (status, result) = commands.getstatusoutput('screen -list|grep builder.%s' % machine)
    #ask if the screen session exists
    if not status:
        emit_message('It appears, screen session to machine is still active, proceed? [y/n]')
        answer = False
        while not answer:
            answer = sys.stdin.readline().rstrip()
            if answer.lower() == 'y':
                answer = True
            else:
                sys.exit(0)
    #try to unmount directories
    machine_chroot =  settings['config']['general']['chroots_top']+'/'+settings['machine']['name']
    proc_mount = machine_chroot + '/proc'
    sys_mount = machine_chroot + '/sys'
    portage_mount = machine_chroot + '/usr/portage'
    _umount(proc_mount)
    _umount(sys_mount)
    _umount(portage_mount)


def _umount(mount_point):
    '''
    Try to umount given mount_point
    '''
    status, result = commands.getstatusoutput('umount %s' % mount_point)
    if status:
        emit_message('umount failed: %s' %result)
    else:
        emit_message('[%s] unmounted OK' % mount_point)

        

def _check_and_mount(what,mount_point,type='bind'):
    '''
    Check if given mount [what] is mounted and mount if it is not.
    '''
    status, result = commands.getstatusoutput('mount|grep  %s' % mount_point)
    if not status :
        emit_message('\t[%s] already mounted .. skipping' % mount_point)
    else:
        emit_message('\tmounting %s at [%s]' % (what,mount_point))
        if type == 'bind':
            mount_command = 'mount -o bind %s %s' % (what, mount_point)
        else:
            mount_command = 'mount -t %s %s %s' % (type,what,mount_point)
        status, result = commands.getstatusoutput(mount_command)
        if status:
            print 'ERROR: unable to mount ..exiting. Reason: \n%s' %result
            sys.exit(2)

def _create_bash_rcfile(rcfile, machine):
    '''
    Creates file for bash initialization (changing hostname)
    '''
    rc_text = """
    . /etc/profile
    export PS1='\\[\\033[01;31m\\]%s\[\\033[01;34m\\] \\W \\$\\[\\033[00m\\] '
    echo 'Happy hacking'
    """ % machine
    f = open(rcfile, 'w')
    f.write(rc_text)
    f.close()

def main():
    #check if user is root
#    if os.getuid() != 0: 
#        print __app__ + ': This script requires root privileges to operate.'
#        sys.exit(2)


    #parse arguments and define action
    usage = 'usage: %prog [options] <machine>'
    parser = OptionParser(usage=usage)
    parser.add_option('-a', '--attach', dest='attachScreen',
            help='creates screen session into the chroot',
            action='store_true', default=False)
    parser.add_option('-d', '--dettach', dest='dettachScreen',
            help='unmounts related directories after screen session is over',
            action='store_true', default=False)
    parser.add_option('-i', '--init', dest='init_machine',
            help='initalizes machine environment',
            action='store_true', default=False)
    parser.add_option('-c', '--config', dest='configFile', 
            help='builder configuration file [/etc/builder/builder.conf]', 
            metavar='configFile', default='etc/builder/builder.conf')
    parser.add_option('-m', '--machine', dest='machineConfig', 
            help='machine configuration file [<configFile>/machines/<machine>.conf]',
            metavar='machineConfig')
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
        machineConfigPath = os.path.dirname(configFile) + '/machines/' + machine + '.conf'
    if not os.path.exists(machineConfigPath) :
        print 'Cannot find machine config %s ..exiting' % machineConfigPath
        sys.exit(2)
    else:
        settings['machine'] = init_settings(configFile=machineConfigPath).dict()
        settings['machine']['name'] = machine

    #dump settings if verbose
    if options.verbose:
        print settings

    #handle actions
    if options.init_machine:
        init_machine(machine)
    if options.attachScreen:
        screen_attach(machine)
    if options.dettachScreen:
        screen_dettach(machine)

#main loop, if called as a program start main
if __name__ == '__main__':
    main()

