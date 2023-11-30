import subprocess
if __name__=="__main__":
    while True:
        input1 = input()
        if(input1[:6]=="bridge"):
            python_script = "Bridge.py"
            script_arguments = input1.split()[1:]
            command = ['start', 'cmd', '/k', 'py', python_script] + script_arguments
            subprocess.run(command, shell=True)
        elif(input1[:11]=="station -no"):
            python_script = "Station.py"
            script_arguments = input1.split()[2:]
            print(script_arguments)
            command = ['start', 'cmd', '/k', 'py', python_script] + script_arguments
            subprocess.run(command, shell=True)
        elif(input1[:11]=="station -ro"):
            python_script = "router.py"
            script_arguments = input1.split()[2:]
            print(script_arguments)
            command = ['start', 'cmd', '/k', 'py', python_script] + script_arguments
            subprocess.run(command, shell=True)