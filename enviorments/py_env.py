from __future__ import annotations
import subprocess
from ..utils import EnvState
from .env import Env
from tempfile import NamedTemporaryFile


class PythonEnv(Env):


    def __init__(self) -> None:
        super().__init__()
        self._name: str = self.__class__.__name__

    def step(self, _command: str, args: list[str] | str = []):

        tmp_code_file = NamedTemporaryFile("w", dir=self.working_dir, suffix=".py", encoding="utf-8")
        # Solving the issue of not being able to retrieve the current working directory of the last line of output
        _command = _command.strip() + "\n"  + "import os" + "\n" + "print(os.getcwd())"
        tmp_code_file.write(_command)
        tmp_code_file.flush()
        filename = tmp_code_file.name
        if isinstance(args, str):
            args = args.split()
        self.env_state = EnvState(command=_command)
        try:
            results = subprocess.run(
                ["python", '-B', str(filename)],
                encoding="utf-8",
                check=True,
                cwd = self.working_dir,
                timeout=self.timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if results.stdout:
                stout = results.stdout.strip().split('\n')
                self.env_state.result = "\n".join(stout[:-1])
                self.observe(stout[-1])
                return self.env_state

        except subprocess.CalledProcessError as e:
            self.env_state.error = e.stderr
        except Exception as e :
            self.env_state.error = repr(e)
        finally:
            tmp_code_file.close()
        self.observe(self.working_dir)

        return self.env_state
    
    def observe(self, pwd):
        self.env_state.pwd = pwd 
        self.working_dir = pwd
        self.env_state.ls = subprocess.run(
            ["ls"],
            cwd = self.working_dir,
            capture_output=True,
            text = True).stdout
        

DEFAULT_DESCRIPRION = """
 def solution():
    print("Hello World")
    print("This is a test")
    return "return"

solution()
"""

if __name__ == '__main__':
    env = PythonEnv()
    print(env.step(DEFAULT_DESCRIPRION))