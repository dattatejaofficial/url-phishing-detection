'''

The setup.py file is an essential part of packaging and distributing Python projects.
It is used by setuptools to define the configuration of your project, such as its meta data, dependencies and more

The __init__.py is a special file used to define packages and initialize the namespaces.
Without this file, Python won't recognize a directory as a package
'''

from setuptools import find_packages,setup
from typing import List
# find_packages scan all the folders and whenever it finds __init__ file, it consider the folder as a package
# setup is responsible for providing all the information about the package

def get_requirements()->List[str]:
    """
    This function will return list of requirements
    """

    requirement_lst:List[str]=[]
    try:
        with open('requirements.txt','r') as file:
            # Read lines from the file
            lines = file.readlines()
            # Process each line
            for line in lines:
                requirement = line.strip()
                # ignore empty lines and -e .
                if requirement and requirement!='-e .':
                    requirement_lst.append(requirement)
    except FileNotFoundError:
        print('requirements.txt file not found')

    return requirement_lst

setup(
    name='Network Security',
    version='0.0.1',
    author='DATTA TEJA',
    author_email='dattateja1234@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements()
)
