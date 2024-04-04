import os 

from typing import Optional, Union, List
from ..utils.schema import EnvState
from ..utils.config import Config

class Env:

    def __init__(self) -> None:

        self._name = self.__class__.__name__
        self.timeout : int = 300
        # working_dir = Config.get_parameter('working_dir')
        working_dir = '/Users/anshulsingh/dev/coplilot'
        if os.path.isabs(working_dir):
            self.working_dir = working_dir
        else:
            self.working_dir = os.path.abspath(os.path.join(__file__, "..", "..", "..", working_dir))
        
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        self.env_state  = None

    def list_working_dir(self):

        directory = self.working_dir    

        if not os.path.exists(directory):
            return f"Directory {directory} does not exist"
        
        files_and_dirs = os.listdir(directory)
        
        details = []

        for name in files_and_dirs:
            full_path = os.path.join(directory, name)

            size = os.path.getsize(full_path)

            if os.path.isdir(full_path):
                doc_type = 'Directory'
            else:
                doc_type = 'File'

            details.append(f"{name}\t {size} bytes\t {doc_type}")

        return "\n".join(details)
    
    def step(self, _command) -> EnvState:
        """
        Executes a command within the environments.

        This method is intended to be implemented by subclasses, defining how commands
        are processed and their effects on the environments state.

        Args:
            _command: The command to be executed.

        Raises:
            NotImplementedError: Indicates that the subclass must implement this method.

        Returns:
            EnvState: The state of the environments after executing the command.
        """
        raise NotImplementedError

    def reset(self):
        """
        Resets the environments to its initial state.

        This method is intended to be implemented by subclasses, defining the specific
        actions required to reset the environments.
        """
        working_dir = Config.get_parameter('working_dir')
        if os.path.isabs(working_dir):
            self.working_dir = working_dir
        else:
            self.working_dir = os.path.abspath(os.path.join(__file__, "..", "..", "..", working_dir))
    
    @property
    def name(self):
        """
        The name of the environments.

        Returns:
            str: The name of the environments, typically set to the class name unless overridden in a subclass.
        """
        return self._name

    def __repr__(self):
        """
        Provides a string representation of the environments.

        Returns:
            str: A representation of the environments, including its name.
        """
        return f'{self.name}'

    def __str__(self):
        """
        Returns the string representation of the environments, mirroring `__repr__`.

        Returns:
            str: A string representation of the environments.
        """
        return self.__repr__()


if __name__ == '__main__':
    env = Env()
    env.env_state = EnvState()
    # result = env.observe()
    


            

