from setuptools import find_packages, setup
from typing import List

def get_requirements() -> List:
    """
    This function returns a list of requirements
    """
    requirement_list : List[str] = []
    try:
        with open('requirements.txt','r') as file:
            lines = file.readlines()

            for line in lines:
                requirement = line.strip()
                if requirement:
                    requirement_list.append(requirement)
    except FileNotFoundError:
        print('requirements.txt file not found')
    
    return requirement_list

setup(
    name='PhishingSystem',
    version='0.0.1',
    author='Datta Teja',
    author_email='dattateja1234@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements()
)