from signal import SIGINT, SIGCONT, SIGSTOP, SIGKILL, SIGTSTP
import signal
from sys import exit
import sys
import os
import subprocess
import shlex
import time

PROMPT = "$ "
EXIT = "exit"
CD = "cd"
PWD = "pwd"
JOBS = "jobs"
BG = "bg"
FG = "fg"
HISTORY = "prev"
HIST_FILENAME = "history.txt"
PIPE = " | "
GOODBYE = "My battery is low and it's getting dark..."
BACKGROUND = "&"
BUILTINS = [CD, PWD, JOBS, BG, FG, HISTORY, EXIT]

#All the current running background jobs will be stored here
bg_processes = []
zombie_processes = []
running_foreground_process = None
foreground_name = ""

def ctrlz(signal_num, frame):
	global running_foreground_process
	print("hello there")
	print(running_foreground_process)
	if running_foreground_process != None:
		print("hello")
		bg_processes.append((running_foreground_process, foreground_name+" —Stopped"))
		os.kill(running_foreground_process.pid, signal.SIGTSTP)
		running_foreground_process = None
		main()

signal.signal(signal.SIGTSTP, ctrlz)

# given the pid in the second argument of uinput,
# returns the process with the corresponding pid
def get_process(uinput):
	global bg_processes
	for i in range(len(bg_processes)):
		p = bg_processes[i][0]
		print("pid: " + str(p.pid))
		print("uninput pid: " + str(uinput[1]))
		if str(p.pid) == str(uinput[1]):
			print("pid = uinput")
			return p
	return None


"""
Handles all the builtin functions; includes:
- exit (exits and prints a sad exit message)
- cd (changes the working directory)
- pwd (prints the working directory)
- jobs (prints the process id and the command per background process)
- bg (restarts the job as a background process)
- fg (restarts the job)
"""
def builtins(uinput, usr = 1):

	if uinput[0] == EXIT:
		print(GOODBYE)
		sys.exit(0)
		return 0

	if uinput[0] == CD:
		# try changing directory; otherwise catch exception
		try:
			os.chdir(uinput[1])
		except Exception as e:
			print("something went wrong :( there's probably no filepath. exception: ", e)
		return os.getcwd()
	
	if uinput[0] == PWD:
		print(os.getcwd())
		return os.getcwd()

	if uinput[0] == JOBS:
		global bg_processes

		# find running background processes
		global zombie_processes
		running_processes = []
		for entry in bg_processes:
			#if process is still runnings
			if entry[0].poll() == None:
				running_processes.append(entry)
			else:
				zombie_processes.append(entry)
		
		for x in zombie_processes:
			sig = x[0].poll() 
			
			if sig != 0:
				print("A signal terminated this shell. The offending signal number was: " + str(sig))
			x[0].terminate()
			#os.kill(x[0].pid, signal.SIGKILL)
		zombie_processes = []
		
		# the user is calling jobs, not fg or bg, then print
		if usr == 1:
			print("pid ", "cmd")
			for i in running_processes:
				print(i[0].pid, i[1])
		bg_processes = running_processes
		return
	
	if uinput[0] == BG:
		#refreshes the list of processes
		builtins([JOBS], 0)
		p = get_process(uinput)
		print(p.pid)
		p.send_signal(signal.SIGCONT)
		# for x in range(0, len(bg_processes)):
		# 	if str(bg_processes[x][0].pid) == uinput[1]:
		# 		bg_processes[x][0].send_signal(signal.SIGCONT)
				#processes[x] = (subprocess.Popen(processes[x][1], shell = True, start_new_session = True), processes[x][1])
		return

	if uinput[0] == FG:
		global fg
		# get jobs list
		builtins([JOBS], 0)

		# loop through find job to restart
		for x in range(0, len(bg_processes)):
			p = bg_processes[x][0]
			if str(p.pid) == uinput[1]:
				p.send_signal(signal.SIGCONT)
				p.communicate()
				#restarted_cmd = processes[x][1]
				bg_processes.pop(x)
				#fg = subprocess.Popen(restarted_cmd, shell = True).wait()
				fg = None
				print("here")
		return

def exec(user_input, background_status):
	global bg_processes
	global running_foreground_process
	global foreground_name
	#MAKES THE LARGE ASSUMPTION THAT ANY BUILTINS ARE PASSED IN IN ISOLATION
	if user_input.split()[0] in BUILTINS:
				#run builtin function	
				p = builtins(user_input.split())
	else:
		#if the process is a background process
		if background_status:
			p = subprocess.Popen(user_input, shell = True, start_new_session = True)
			bg_processes.append((p, user_input))
		else:
			#The process is a foreground process
			running_foreground_process = subprocess.Popen(user_input, shell = True)
			print(running_foreground_process.pid)
			foreground_name = user_input
			running_foreground_process.wait()
	return
		
def get_user_input():
	background_process = False

	# Initially assuming that the user will ask for a  
	# process incorrectly
	good_user_input = False

	# keep getting user input until happy
	while not good_user_input:
		builtins([JOBS], 0)
		user_input = input(PROMPT)
		#Just checking to see if the user even entered a string
		if len(user_input) >= 2:
			good_user_input = True
	#seeing if the command is a background process
	if user_input[-1] == BACKGROUND and user_input[-2] == " ":
		background_process = True
		user_input = user_input[:-2]
	return (user_input, background_process)

def main():
	global zombie_processes
	global running_foreground_process
	
	# main loop
	while(True):
		try:
			user_input, background_status = get_user_input()
			exec(user_input, background_status)

		except KeyboardInterrupt:
			if running_foreground_process != None:
				print("in c if")
				print(running_foreground_process.pid)
				running_foreground_process.send_signal(signal.SIGINT)
				running_foreground_process = None
	return

main()