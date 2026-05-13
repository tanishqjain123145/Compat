from compat.runtime import runtime

@runtime(requirements=r"runtimes\click_new.txt")
def ps(all_processes=False):
    import subprocess
    command = ["tasklist", "/v"] if all_processes else ["tasklist"]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

@runtime(requirements=r"runtimes\click_old.txt")
def ps_old(all_processes=False):
    import subprocess
    command = ["tasklist", "/v"] if all_processes else ["tasklist"]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

if __name__ == "__main__":
    output = ps()
    output2 = ps_old()
    print("Output from ps():")
    print(output)
    print("Output from ps_old():")
    print(output2)