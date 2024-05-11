#!/bin/bash
source /home/david/alarm/bin/activate
echo "Running pipreqs from script" >> /home/david/alarm/script.log
# Generate requirements.txt for Python project
cd /home/david/alarm/src
/home/david/alarm/bin/pipreqs . --ignore bin,lib,include,share,__pycache__ --force
echo "Script completed" >> /home/david/alarm/script.log
deactivate
