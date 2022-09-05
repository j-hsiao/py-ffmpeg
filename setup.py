from setuptools import setup
from jhsiao.namespace import make_ns, fdir

make_ns('jhsiao', dir=fdir(__file__))
setup(
    name='jhsiao-ffmpeg',
    version='0.0.1',
    author='Jason Hsiao',
    author_email='oaishnosaj@gmail.com',
    description='read from/write to ffmpeg subprocess',
    packages=['jhsiao', 'jhsiao.ffmpeg'],
    install_requires=[
        'jhsiao-utils @ git+https://github.com/j-hsiao/py-utils.git',
        'numpy',
        'opencv-python']
)
