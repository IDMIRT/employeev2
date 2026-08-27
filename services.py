import subprocess


def check_docker():
        
    try:
        subprocess.run(['docker', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print("Docker установлен")
        return True
    except subprocess.CalledProcessError:
        subprocess.check_call(["winget", "install", "docker-desktop"])
        return True
    except Exception as e:
        # print(f"Произошла ошибка: {e}")
        return False, f"Произошла ошибка: {e}"