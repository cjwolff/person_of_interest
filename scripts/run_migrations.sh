#!/bin/bash
cd /opt/person_of_interest
source /root/miniconda3/etc/profile.d/conda.sh
conda activate poi
alembic upgrade head
